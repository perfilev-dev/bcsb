import sys
import unittest

from os import path, environ

# Export dir for import module like from root directory
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from util import configure_for_unittest
from telegram import (Bot, Update, Message, Chat,
                      ReplyKeyboardMarkup, ReplyKeyboardHide)


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
        configure_for_unittest()
        from command import start

        bot = FakeBot()
        upd = FakeUpdate(message=FakeMessage(chat=FakeChat(id=1)))

        start(bot, upd)

        self.assertTrue('You' in bot.sended_message['text'])
        self.assertEqual(bot.sended_message['chat_id'], 1)
        self.assertEqual(type(bot.sended_message['reply_markup']), ReplyKeyboardHide)
