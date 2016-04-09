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

    titles = [s.title for s in shared.session.query(Show)]

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(titles))


def subscribe(bot, update):
    ''' Subscribes chat on the show. '''

    title = update.message.text.split('/subscribe ')[1].strip().lower()

    show = shared.session.query(Show).filter(Show.title_lower == title).first()
    chat = shared.session.query(Chat).filter(Chat.id == update.message.chat_id).first()

    if not show is None:

        if chat is None:
            chat = Chat(id=update.message.chat_id)
            shared.session.save(chat)
        else:
            try:
                subs = shared.session.query(Subscription).filter(
                    Subscription.chat == chat, Subscription.show == show).first()
            except Exception as e:
                print e
            if not subs is None:
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="You're already subscribed!")
                return

        subs = Subscription(chat=chat, show=show)
        shared.session.save(subs)

        bot.sendMessage(chat_id=update.message.chat_id,
                        text="You're subscribed to the '%s'!" % show.title)
    else:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Wrong title!")
