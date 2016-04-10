import __builtin__ as shared

from telegram import Bot
from telegram.ext import Updater
from mongoalchemy.session import Session
from utils.config import configure_from_file
from methods import start, showlist, subscribe, unsubscribe, subscriptions
from gettext import translation


if __name__ == '__main__':
    shared.config = configure_from_file('default.cfg')
    shared.session = Session.connect(shared.config['database']['name'], safe=True)
    shared.lang = {
        'en': translation('default', localedir='locale', languages=['en']),
        'ru': translation('default', localedir='locale', languages=['ru'])
    }
    shared.lang['en'].install() # Temporary !!!

    updater = Updater(token=shared.config['telegram']['token'])

    dispatcher = updater.dispatcher
    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('showlist', showlist)
    dispatcher.addTelegramCommandHandler('subscribe', subscribe)
    dispatcher.addTelegramCommandHandler('unsubscribe', unsubscribe)
    dispatcher.addTelegramCommandHandler('subscriptions', subscriptions)

    updater.start_polling()
