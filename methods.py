import __builtin__ as shared

from models import Show, Season, Episode, Chat, Subscription


def start(bot, update):
    ''' Mandatory method according to Telegram API. '''

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(['/showlist',
                                    '/subscribe',
                                    '/unsubscribe']))


def showlist(bot, update):
    ''' Show the list of available TV shows. '''

    show_titles = [s.title for s in shared.session.query(Show)]

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(show_titles))


def subscribe(bot, update):
    ''' Subscribes chat on the show. '''

    try:
        show_title = update.message.text.split('/subscribe ')[1].strip().lower()

        show = shared.session.query(Show).filter(Show.title_lower == show_title).first()

        if not show is None:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="You're subscribed to the %s" % show.title)
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="Wrong show title")
    except Exception as e:
        print e
