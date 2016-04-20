# coding: utf8

import sys
import unittest

from os import path, environ
from datetime import datetime as dt

# Export dir for import module like from root directory
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from util import configure_for_unittest
from telegram import (Bot, Update, Message, Chat,
                      Emoji, ReplyKeyboardMarkup, ReplyKeyboardHide)


class FakeChat(Chat):
    def __init__(self, *args, **kwargs):
        self.id = kwargs['id']

class FakeMessage(Message):
    def __init__(self, *args, **kwargs):
        self.chat = kwargs['chat']

class FakeBot(Bot):
    def __init__(self, *args, **kwargs):
        pass

    def sendMessage(self, *args, **kwargs):
        self.sended_message = kwargs

class FakeUpdate(Update):
    def __init__(self, *args, **kwargs):
        self.message = kwargs['message']


class TestCommand(unittest.TestCase):

    def test_start(self):
        ''' Tests response on start request. '''

        configure_for_unittest()
        from command import start

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        start(bot, upd)

        self.assertTrue('You can control' in bot.sended_message['text'])
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

    def test_showlist(self):
        ''' Tests response on showlist request. '''

        configure_for_unittest()
        from command import showlist
        from model import Show, Chat

        show1 = Show(title='House of Cards').save()
        show2 = Show(title='Teacher Gym').save()
        chat = Chat(id=1).save()

        chat.subscriptions.connect(show1)

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        showlist(bot, upd)

        lines = ('Available TV shows:\n',
                 '▪ House of Cards',
                 '▫ Teacher Gym')

        self.assertEqual(bot.sended_message['text'], '\n'.join(lines))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

    def test_subscriptions(self):
        ''' Tests responses on subscriptions request. '''

        configure_for_unittest()
        from command import subscriptions
        from model import Show, Chat

        show1 = Show(title='House of Cards').save()
        show2 = Show(title='Teacher Gym').save()
        chat = Chat(id=1).save()

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        # if there is at least one subscription
        chat.subscriptions.connect(show1)
        subscriptions(bot, upd)

        lines = ('Active subscriptions:\n',
                 '▪ House of Cards')

        self.assertEqual(bot.sended_message['text'], '\n'.join(lines))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # if no subscriptions
        chat.subscriptions.disconnect(show1)
        subscriptions(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You are not subscribed to any of the series.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

    def test_subscribe(self):
        ''' Tests responses on subscribe request. '''

        configure_for_unittest()
        from command import subscribe
        from model import Show, Chat

        show1 = Show(title='House of Cards').save()
        show2 = Show(title='Teacher Gym').save()
        chat = Chat(id=1).save()

        chat.subscriptions.connect(show1)

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        # valid request
        upd.message.text = '/subscribe teacher gym'
        subscribe(bot, upd)

        self.assertTrue(chat in show2.subscribers.all())
        self.assertEqual(bot.sended_message['text'], _('You have subscribed to the show.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to subscript twice
        upd.message.text = '/subscribe house of cards'
        subscribe(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You are already subscribed to this series.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to subscript for non-existent TV show
        upd.message.text = '/subscribe kitchen'
        subscribe(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Specified series is not on my list.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

    def test_unsubscribe(self):
        ''' Tests responses on unsubscirbe request. '''

        configure_for_unittest()
        from command import unsubscribe
        from model import Show, Chat

        show1 = Show(title='House of Cards').save()
        show2 = Show(title='Teacher Gym').save()
        chat = Chat(id=1).save()

        chat.subscriptions.connect(show1)

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        # valid request
        upd.message.text = '/unsubscribe house of cards'
        unsubscribe(bot, upd)

        self.assertFalse(chat in show1.subscribers.all())
        self.assertEqual(bot.sended_message['text'], _('You have unsubscribed from the show.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to cancel non-existent subscription
        upd.message.text = '/unsubscribe house of cards'
        unsubscribe(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You are not subscribed to the show.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to unsubscript for non-existent TV show
        upd.message.text = '/unsubscribe kitchen'
        unsubscribe(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Specified series is not on my list.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

    def test_setlanguage(self):
        ''' Tests responses on setlanguage request. '''

        configure_for_unittest()
        from command import setlanguage
        from model import Chat

        chat = Chat(id=1).save()

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        # valid request
        upd.message.text = '/setlanguage ru'
        setlanguage(bot, upd)

        chat.refresh()

        self.assertEqual(chat.language, 'ru')
        self.assertEqual(bot.sended_message['text'], _('The language has changed!'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to set non-existent language
        upd.message.text = '/setlanguage de'
        setlanguage(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Unknown language!'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to set same language
        upd.message.text = '/setlanguage ru'
        setlanguage(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You are already using this language!'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

    def test_watch(self):
        ''' Tests responses on watch request. '''

        configure_for_unittest()
        from command import watch
        from model import Chat, Show, Season, Episode, Video

        chat = Chat(id=1).save()

        show = Show(title='House of Cards').save()
        season1 = Season(show=show, number=1).save()
        season2 = Season(show=show, number=2).save()
        episode1 = Episode(season=season1, number=1, release_date=dt(2010,1,1)).save()
        episode2 = Episode(season=season1, number=2).save()
        episode3 = Episode(season=season2, number=1).save()
        video1 = Video(link='link to video').save()
        video2 = Video(link='one more link').save()

        show.seasons.connect(season1)
        show.seasons.connect(season2)
        season1.episodes.connect(episode1)
        season1.episodes.connect(episode2)
        season2.episodes.connect(episode3)
        episode1.videos.connect(video1)
        episode1.videos.connect(video2)
        chat.rated_videos.connect(video1, {'value': 1})

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        # valid request
        upd.message.text = '/watch house of cards s1 e1'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], 'link to video')
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardMarkup)
        self.assertEqual(bot.sended_message['reply_markup'].keyboard, [[Emoji.THUMBS_UP_SIGN,
                                                                        Emoji.THUMBS_DOWN_SIGN]])

        chat.referer = ''
        chat.save()

        # valid request - without arguments
        upd.message.text = '/watch'
        watch(bot, upd)

        chat.refresh()

        self.assertEqual('/watch', chat.referer)
        self.assertEqual(bot.sended_message['text'], _('Which TV show would you like to see?'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # valid request - continue with show_title
        upd.message.text = ' '.join([chat.referer, 'house of cards'])
        watch(bot, upd)

        chat.refresh()

        self.assertEqual(chat.referer, '/watch house of cards')
        self.assertEqual(bot.sended_message['text'], _('Which season would you like to see?'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardMarkup)
        self.assertEqual(bot.sended_message['reply_markup'].keyboard, [['1']])

        # valid request - continue with seasons number
        upd.message.text = ' '.join([chat.referer, 's1'])
        watch(bot, upd)

        chat.refresh()

        self.assertEqual(chat.referer, '/watch house of cards s1')
        self.assertEqual(bot.sended_message['text'], _('Which episode would you like to see?'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardMarkup)
        self.assertEqual(bot.sended_message['reply_markup'].keyboard, [['1']])

        # valid request - continue with episode number
        upd.message.text = ' '.join([chat.referer, 'e1'])
        watch(bot, upd)

        chat.refresh()

        self.assertEqual(chat.referer, '/rate link to video')
        self.assertEqual(bot.sended_message['text'], 'link to video')
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardMarkup)
        self.assertEqual(bot.sended_message['reply_markup'].keyboard, [[Emoji.THUMBS_UP_SIGN,
                                                                        Emoji.THUMBS_DOWN_SIGN]])

        chat.referer = ''
        chat.save()

        # trying to watch non-existent TV show
        upd.message.text = '/watch kitchen'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('This TV show is not available.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to watch non-existent season
        upd.message.text = '/watch house of cards s5'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('This season is not available.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to watch unavailable season
        upd.message.text = '/watch house of cards s2 e1'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('This season is not available.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to watch non-existent episode
        upd.message.text = '/watch house of cards s1 e5'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('This episode is not available.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # trying to watch unavailable episode
        upd.message.text = '/watch house of cards s1 e2'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('This episode is not available.'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)


class TestMessage(unittest.TestCase):

    def test_default(self):
        ''' Tests responses on messages that are not commands. '''

        configure_for_unittest()
        from command import default, subscribe, unsubscribe, setlanguage, watch
        from model import Chat, Show, Season, Episode, Video

        chat = Chat(id=1).save()

        show = Show(title='House of Cards').save()
        season1 = Season(show=show, number=1).save()
        season2 = Season(show=show, number=2).save()
        episode1 = Episode(season=season1, number=1, release_date=dt(2010,1,1)).save()
        episode2 = Episode(season=season1, number=2).save()
        episode3 = Episode(season=season2, number=1).save()
        video1 = Video(link='link to video').save()
        video2 = Video(link='one more link').save()

        show.seasons.connect(season1)
        show.seasons.connect(season2)
        season1.episodes.connect(episode1)
        season1.episodes.connect(episode2)
        season2.episodes.connect(episode3)
        episode1.videos.connect(video1)
        episode1.videos.connect(video2)
        chat.rated_videos.connect(video1, {'value': 1})

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        # random input
        upd.message.text = 'random input'
        default(bot, upd)

        self.assertTrue('You can control' in bot.sended_message['text'])

        # subscribe in 2 steps
        upd.message.text = '/subscribe'
        subscribe(bot, upd)

        upd.message.text = 'house of cards'
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You have subscribed to the show.'))

        # unsubscribe in 2 steps
        upd.message.text = '/unsubscribe'
        unsubscribe(bot, upd)

        upd.message.text = 'house of cards'
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You have unsubscribed from the show.'))

        # setlanguage in 2 steps
        upd.message.text = '/setlanguage'
        setlanguage(bot, upd)

        upd.message.text = 'en'
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('You are already using this language!'))

        # watch in 4 steps
        upd.message.text = '/watch'
        watch(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Which TV show would you like to see?'))

        upd.message.text = 'house of cards'
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Which season would you like to see?'))

        upd.message.text = '1'
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Which episode would you like to see?'))

        upd.message.text = '1'
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], 'link to video')

        chat.referer = ''
        chat.save()

        # positive review - say 'thank you'
        upd.message.text = '/watch house of cards s1 e1'
        watch(bot, upd)

        upd.message.text = Emoji.THUMBS_UP_SIGN
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], _('Thanks for the feedback!'))
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)

        # negative review - return other link to video
        upd.message.text = '/watch house of cards s1 e1'
        watch(bot, upd)

        chat.refresh()

        upd.message.text = Emoji.THUMBS_DOWN_SIGN
        default(bot, upd)

        self.assertEqual(bot.sended_message['text'], 'one more link')
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardMarkup)
        self.assertEqual(bot.sended_message['reply_markup'].keyboard, [[Emoji.THUMBS_UP_SIGN,
                                                                        Emoji.THUMBS_DOWN_SIGN]])


if __name__ == '__main__':
    unittest.main()
