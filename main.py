import __builtin__ as shared

from telegram import Bot
from telegram.ext import Updater
from utils.config import configure_from_file
from methods import start, showlist


if __name__ == '__main__':
    shared.config = configure_from_file('default.cfg')

    updater = Updater(token=shared.config['telegram']['token'])

    dispatcher = updater.dispatcher
    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('showlist', showlist)

    updater.start_polling()
