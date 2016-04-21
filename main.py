import __builtin__ as shared

from telegram import Bot
from telegram.ext import Updater
from util import configure_from_file

# configure for normal mode
configure_from_file('default.cfg')

from worker import Notifier
from command import (start, showlist, setlanguage, subscribe, unsubscribe,
                     subscriptions, default, watch)


if __name__ == '__main__':

    updater = Updater(token=shared.config['telegram']['token'])
    dispatcher = updater.dispatcher

    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('showlist', showlist)
    dispatcher.addTelegramCommandHandler('setlanguage',setlanguage)
    dispatcher.addTelegramCommandHandler('subscribe',subscribe)
    dispatcher.addTelegramCommandHandler('unsubscribe',unsubscribe)
    dispatcher.addTelegramCommandHandler('subscriptions',subscriptions)
    dispatcher.addTelegramCommandHandler('watch',watch)
    dispatcher.addTelegramMessageHandler(default)

    # start command handler
    updater.start_polling()

    # start notifier
    Notifier(bot=updater.bot).start()
