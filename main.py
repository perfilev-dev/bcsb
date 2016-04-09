import __builtin__ as shared

from telegram import Bot
from telegram.ext import Updater
from mongoalchemy.session import Session
from utils.config import configure_from_file
from methods import start, showlist, subscribe


if __name__ == '__main__':
    shared.config = configure_from_file('default.cfg')
    shared.session = Session.connect(shared.config['database']['name'],
                                     safe=True)

    updater = Updater(token=shared.config['telegram']['token'])

    dispatcher = updater.dispatcher
    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('showlist', showlist)
    dispatcher.addTelegramCommandHandler('subscribe', subscribe)

    updater.start_polling()
