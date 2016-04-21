import __builtin__ as shared

from time import sleep
from threading import Thread
from model import Chat, Show, Episode
from datetime import datetime as dt
from parsers import add_or_update_show, update_episode_urls
from telegram import ReplyKeyboardHide, ReplyKeyboardMarkup, Emoji
from neomodel import DoesNotExist


class ShowFinder(Thread):
    def __init__(self, bot, chat_id, show_title):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.chat_id = chat_id
        self.show_title = show_title

    def run(self):

        # try to add the non-existent show
        add_or_update_show(self.show_title.encode('utf-8'))

        try:
            show = Show.nodes.get(title_lower=self.show_title)
            response = _('We\'ve found a show "%s" that you are looking for.') % self.show_title
        except DoesNotExist:
            response = _('We can\'t found a show "%s" that you are looking for.') % self.show_title

        self.bot.sendMessage(chat_id=self.chat_id,
                             text=response,
                             reply_markup=ReplyKeyboardHide())


class VideoFinder(Thread):
    def __init__(self, bot, chat_id, episode):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.chat_id = chat_id
        self.episode = episode

    def run(self):

        chat = Chat.get_or_create(self.chat_id)
        videos = set(self.episode.videos)

        # select chat rated videos
        chat_rated_videos = set([v for v in videos if chat in v.critics])

        # if rating is positive, return this video, otherwise return the best video
        if any([v.critics.relationship(chat).value > 0 for v in chat_rated_videos]):
            videos = [v for v in chat_rated_videos if v.critics.relationship(chat).value > 0]
        else:
            videos = sorted(videos-chat_rated_videos, key=lambda x: -x.score)

        reply_markup = ReplyKeyboardMarkup([[Emoji.THUMBS_UP_SIGN,
                                             Emoji.THUMBS_DOWN_SIGN]])

        if videos:
            response = videos[0].link
            chat.referer = '/rate ' + response
        elif update_episode_urls(self.episode):
            response = self.episode.videos.all()[0].link
            chat.referer = '/rate ' + response
        else:
            response = _('We could not found any video of the episode.')
            reply_markup = ReplyKeyboardHide()
            chat.referer = ''

        self.bot.sendMessage(chat_id=self.chat_id,
                             text=response,
                             reply_markup=reply_markup)
        chat.save()


class Notifier(Thread):
    def __init__(self, bot, interval=60*60):
        Thread.__init__(self)
        self.daemon = True
        self.interval = interval
        self.bot = bot

    def run(self):

        # loop forever
        while True:

            # find episode that unshown and release_date < dt.now()
            unshown_episodes = Episode.nodes.filter(release_date__lt=dt.now(),
                                                    is_already_shown=False)

            for episode in unshown_episodes:
                for chat in episode.show.get().subscribers:
                    VideoFinder(bot=self.bot,
                                chat_id=chat.id,
                                episode=episode).start()

                episode.is_already_shown = True
                episode.save()

            sleep(self.interval)
