import methods
import __builtin__ as shared

from telegram import Bot
from telegram.ext import Updater
from utils.config import configure_from_file


if __name__ == '__main__':

    shared.config = configure_from_file('default.cfg')

    for lang in shared.config['telegram']['lang']




    shared.config = configure_from_file('default.cfg')
    shared.session = Session.connect(shared.config['database']['name'], safe=True)
    shared.lang = {
        'en': translation('default', localedir='locale', languages=['en']),
        'ru': translation('default', localedir='locale', languages=['ru'])
    }

    updater = Updater(token=shared.config['telegram']['token'])
    dispatcher = updater.dispatcher

    dispatcher.addTelegramMessageHandler(methods.default)
    for command in methods.__all__:
        if command != 'default':
            dispatcher.addTelegramCommandHandler(command, getattr(methods, command))

    updater.start_polling()
