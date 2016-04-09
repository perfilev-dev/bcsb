import __builtin__ as shared

from models import Show, Season, Episode, Chat, Subscription


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text='\n'.join(['/showlist', '/subscribe', '/unsubscribe']))
