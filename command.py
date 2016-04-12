import __builtin__ as shared

from model import Chat, Show, Season, Episode
from telegram import Emoji, ReplyKeyboardMarkup, ReplyKeyboardHide


def start(bot, update):
    ''' Returns the standard greeting with a list of commands. '''

    chat = Chat.get_or_create(id=update.message.chat_id)

    response = (
        _('You can control me by sending these commands:') + '\n',
        '/showlist - %s' % _('show list of available TV shows'),
        '/subscriptions - %s' % _('show active subscriptions'),
        '/subscribe - %s' % _('subscribe to a TV show'),
        '/unsubscribe - %s' % _('unsubscribe from a TV show'),
        '/setlang - %s' % _('change language')
    )

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(response),
                    reply_markup=ReplyKeyboardHide())
