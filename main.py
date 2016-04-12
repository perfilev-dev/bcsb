import __builtin__ as shared

from telegram import Bot
from telegram.ext import Updater
from util import configure_from_file

# Configure bot for normal mode
configure_from_file('default.cfg')

from command import start


if __name__ == '__main__':

    updater = Updater(token=shared.config['telegram']['token'])
    dispatcher = updater.dispatcher

    dispatcher.addTelegramCommandHandler('start', start)

    updater.start_polling()
