import re
import __builtin__ as shared

from neomodel import DoesNotExist
from model import Chat, Show, Season, Episode, Video
from telegram import Emoji, ReplyKeyboardMarkup, ReplyKeyboardHide
from worker import ShowFinder, VideoFinder


def start(bot, update):
    ''' Returns the standard greeting with a list of commands. '''

    chat = Chat.get_or_create(id=update.message.chat_id)
    chat.referer = ''
    chat.save()

    response = (
        _('You can control me by sending these commands:') + '\n',
        '/showlist - %s' % _('show list of available TV shows'),
        '/subscriptions - %s' % _('show active subscriptions'),
        '/subscribe - %s' % _('subscribe to a TV show'),
        '/unsubscribe - %s' % _('unsubscribe from a TV show'),
        '/setlanguage - %s' % _('change language'),
        '/watch - %s' % _('find any available episode')
    )

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(response),
                    reply_markup=ReplyKeyboardHide())

def showlist(bot, update):
    ''' Returns list of available TV shows. '''

    chat = Chat.get_or_create(id=update.message.chat_id)
    chat.referer = ''
    chat.save()

    response_lines = [ unicode(_('List of available TV shows:') + '\n', 'utf-8')
    ] + [' '.join([unicode(Emoji.BLACK_SMALL_SQUARE if chat in s.subscribers.all()
                                            else Emoji.WHITE_SMALL_SQUARE, 'utf-8'),
                   s.title]) for s in sorted(Show.nodes.all(),
                                             key=lambda x: x.title)]

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(response_lines),
                    reply_markup=ReplyKeyboardHide())

def subscriptions(bot, update):
    ''' Returns active subscriptions of the chat. '''

    chat = Chat.get_or_create(id=update.message.chat_id)
    chat.referer = ''
    chat.save()

    if chat.subscriptions.all():

        response_lines = [ unicode(_('Active subscriptions:') + '\n', 'utf-8')
        ] + [' '.join([unicode(Emoji.BLACK_SMALL_SQUARE, 'utf-8'),
                       s.title]) for s in sorted(chat.subscriptions.all(),
                                                 key=lambda x: x.title)]
        response = '\n'.join(response_lines)
    else:
        response = _('You are not subscribed to any of the series.')

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=ReplyKeyboardHide())

def subscribe(bot, update):
    ''' Provides user subscription. '''

    chat = Chat.get_or_create(id=update.message.chat_id)

    show_title = update.message.text[11:].strip().lower()

    if show_title:
        try:
            show = Show.nodes.get(title_lower=show_title)

            if chat in show.subscribers.all():
                response = _('You are already subscribed to this series.')
            else:
                show.subscribers.connect(chat)
                response = _('You have subscribed to the show.')
        except DoesNotExist:
            response = _('Specified series is not on my list, '
                         'but we will try to find this series.')
            ShowFinder(bot=bot,
                       chat_id=update.message.chat_id,
                       show_title=show_title).start()
        chat.referer = ''
    else:
        response = _('Which series would you like to subscribe?')
        chat.referer = update.message.text

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=ReplyKeyboardHide())
    chat.save()

def unsubscribe(bot, update):
    ''' Provides user unsubscription. '''

    chat = Chat.get_or_create(id=update.message.chat_id)

    show_title = update.message.text[13:].strip().lower()

    if show_title:
        try:
            show = Show.nodes.get(title_lower=show_title)

            if chat in show.subscribers.all():
                show.subscribers.disconnect(chat)
                response = _('You have unsubscribed from the show.')
            else:
                response = _('You are not subscribed to the show.')

        except DoesNotExist:
            response = _('Specified series is not on my list.')
        chat.referer = ''
    else:
        response = _('Which series would you like to unsubscribe?')
        chat.referer = update.message.text

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=ReplyKeyboardHide())
    chat.save()

def setlanguage(bot, update):
    ''' Provides the setting of language preferences. '''

    chat = Chat.get_or_create(id=update.message.chat_id)

    language = update.message.text[13:].strip().lower()

    reply_markup=ReplyKeyboardHide()

    if language:
        if language in shared.translations:
            if chat.language != language:
                chat.language = language
                chat.save()
                response = _('The language has changed!')
            else:
                response = _('You are already using this language!')
        else:
            response = _('Unknown language!')
        chat.referer = ''
    else:
        response = _('Which language do you prefer?')
        reply_markup = ReplyKeyboardMarkup([shared.config['telegram']['locales']])
        chat.referer = update.message.text

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=reply_markup)
    chat.save()

def watch(bot, update):
    ''' Returns a link to the video of episode. '''

    def parse(text):
        matches = [re.search(r'/watch (.+) s(\d+) e(\d+)', text),
                   re.search(r'/watch (.+) s(\d+)', text),
                   re.search(r'/watch (.+)', text)]

        if not matches[0] is None:
            show_title, season_number, episode_number = matches[0].group(1,2,3)
        elif not matches[1] is None:
            show_title, season_number, episode_number = matches[1].group(1,2) + (None,)
        elif not matches[2] is None:
            show_title, season_number, episode_number = (matches[2].group(1), None, None)
        else:
            show_title, season_number, episode_number = ('', None, None)

        return show_title.strip().lower(), season_number, episode_number

    chat = Chat.get_or_create(id=update.message.chat_id)

    response, reply_markup = None, ReplyKeyboardHide()

    if not chat.referer:
        show_title, season_number, episode_number = parse(update.message.text)
    else:
        show_title, season_number, episode_number = parse(chat.referer)

        if not show_title:
            show_title = update.message.text[7:].strip().lower()
        elif not season_number:
            try:
                season_number = int(update.message.text.split(chat.referer + ' s')[1])
            except ValueError:
                response = _('Invalide season number.')
        else:
            try:
                episode_number = int(update.message.text.split(chat.referer + ' e')[1])
            except ValueError:
                response = _('Invalid episode number.')

    if not response:
        if show_title:
            try:
                show = Show.nodes.get(title_lower=show_title)

                if show.is_available:
                    if season_number:
                        try:
                            season = show.seasons.get(number=season_number)

                            if season.is_available:
                                if episode_number:
                                    try:
                                        episode = season.episodes.get(number=episode_number)

                                        if episode.is_available:

                                            response = _('We will send you video soon.')
                                            chat.referer = update.message.text

                                            VideoFinder(bot=bot,
                                                        chat_id=update.message.chat_id,
                                                        episode=episode).start()

                                        else:
                                            raise DoesNotExist({'episode_number': episode_number})
                                    except DoesNotExist:
                                        response = _('This episode is not available.')
                                        chat.referer = ''
                                else:
                                    response = _('Which episode would you like to see?')
                                    chat.referer, l = update.message.text, sorted(
                                        [str(ep.number) for ep in season.available_episodes],
                                        key=lambda x: int(x))
                                    reply_markup = ReplyKeyboardMarkup(
                                        [l[i:i+3] for i in range(0,len(l),3)])
                            else:
                                raise DoesNotExist({'season_number': season_number})
                        except DoesNotExist:
                            response = _('This season is not available.')
                            chat.referer = ''
                    else:
                        response = _('Which season would you like to see?')
                        chat.referer, l = update.message.text, sorted(
                            [str(s.number) for s in show.available_seasons],
                            key=lambda x: int(x))
                        reply_markup = ReplyKeyboardMarkup(
                            [l[i:i+3] for i in range(0,len(l),3)])
                else:
                    raise DoesNotExist({'show_title': show_title})
            except DoesNotExist:
                response = _('Specified series is not on my list, '
                             'but we will try to find this series.')
                ShowFinder(bot=bot,
                           chat_id=update.message.chat_id,
                           show_title=show_title).start()
        else:
            response = _('Which TV show would you like to see?')
            chat.referer = update.message.text

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=reply_markup)
    chat.save()

def rate(bot, update):
    ''' Provides the ability to rate videos. '''

    chat = Chat.get_or_create(id=update.message.chat_id)
    video = Video.nodes.get(url=' '.join(update.message.text[6:].split()[:-1]))

    chat.rated_videos.disconnect(video)
    ref, chat.referer = chat.referer, ''
    chat.save()

    if update.message.text.split()[-1] == unicode(Emoji.THUMBS_UP_SIGN, 'utf-8'):
        chat.rated_videos.connect(video, {'value': 1})
        bot.sendMessage(chat_id=update.message.chat_id,
                        text= _('Thanks for the feedback!'),
                        reply_markup=ReplyKeyboardHide())
    elif update.message.text.split()[-1] == unicode(Emoji.THUMBS_DOWN_SIGN, 'utf-8'):
        chat.rated_videos.connect(video, {'value': -1})
        update.message.text = ' '.join(['/watch', video.episode.get().id])
        watch(bot, update)
    else:
        chat.referer = ref
        chat.save()
        bot.sendMessage(chat_id=update.message.chat_id,
                        text= _('Please rate the video.'),
                        reply_markup = ReplyKeyboardMarkup([
                            [Emoji.THUMBS_UP_SIGN, Emoji.THUMBS_DOWN_SIGN]]))

def default(bot, update):
    ''' Handles messages that are not commands. '''

    chat = Chat.get_or_create(id=update.message.chat_id)

    if chat.referer.startswith('/subscribe'):
        update.message.text = ' '.join([chat.referer, update.message.text])
        subscribe(bot, update)
    elif chat.referer.startswith('/unsubscribe'):
        update.message.text = ' '.join([chat.referer, update.message.text])
        unsubscribe(bot, update)
    elif chat.referer.startswith('/setlanguage'):
        update.message.text = ' '.join([chat.referer, update.message.text])
        setlanguage(bot, update)
    elif chat.referer.startswith('/rate'):
        update.message.text = ' '.join([chat.referer, update.message.text])
        rate(bot, update)
    elif chat.referer.startswith('/watch'):
        pairs = re.findall(r'([a-z]+)([0-9]+)', chat.referer)
        update.message.text = (' %s' % (
            '' if chat.referer == '/watch' else 'e' if pairs else 's')).join([
                chat.referer, update.message.text])
        watch(bot, update)
    else:
        start(bot, update)
