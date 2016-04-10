import __builtin__ as shared

from telegram import Emoji
from models import Show, Chat, Subscription


def start(bot, update):
    ''' Mandatory method according to Telegram API. '''

    response = (
        _('You can control me by sending these commands:') + '\n',
        '/showlist - %s' % _('show list of available TV shows'),
        '/subscribe - %s' % _('subscribe to a TV show'),
        '/unsubscribe - %s' % _('unsubscribe from a TV show'),
        '/subscriptions - %s' % _('show active subscriptions')
    )

    bot.sendMessage(chat_id=update.message.chat_id, text='\n'.join(response))


def showlist(bot, update):
    ''' Show the list of available TV shows. '''

    response = [ _('List of available TV shows:') + '\n' ]

    chat = shared.session.query(Chat).filter(Chat.id == update.message.chat_id).first()
    titles = sorted([(x.mongo_id,
                      x.title.encode('utf8')) for x in shared.session.query(Show)],
                     key=lambda x: x[1])
    ids = []
    if not chat is None:
        ids = [x.show.mongo_id for x in shared.session.query(Subscription).filter(
            Subscription.chat.mongo_id == chat.mongo_id)]

    response += [' '.join([
        Emoji.BLACK_SMALL_SQUARE if title[0] in ids else Emoji.WHITE_SMALL_SQUARE,
        title[1]
    ]) for title in titles]

    bot.sendMessage(chat_id=update.message.chat_id, text='\n'.join(response))


def subscribe(bot, update):
    ''' Subscribes chat on the show. '''

    title = update.message.text[11:].strip().lower()

    show = shared.session.query(Show).filter(Show.title_lower == title).first()
    chat = shared.session.query(Chat).filter(Chat.id == update.message.chat_id).first()

    if show is None:
        response = _('Specified series is not on my list.')
    else:
        if chat is None:
            chat = Chat(id=update.message.chat_id)
            subs = Subscription(chat=chat, show=show)
            shared.session.save(chat)
            shared.session.save(subs)
            response = _('You have subscribed to the show.')
        else:
            subs = shared.session.query(Subscription).filter(
                Subscription.show.mongo_id == show.mongo_id,
                Subscription.chat.mongo_id == chat.mongo_id).first()
            if not subs is None:
                response = _('You are already subscribed to this series.')
            else:
                subs = Subscription(chat=chat, show=show)
                shared.session.save(subs)
                response = _('You have subscribed to the show.')

    bot.sendMessage(chat_id=update.message.chat_id, text=response)


def unsubscribe(bot, update):
    ''' Unubscribes chat from the show. '''

    title = update.message.text[13:].strip().lower()

    show = shared.session.query(Show).filter(Show.title_lower == title).first()
    chat = shared.session.query(Chat).filter(Chat.id == update.message.chat_id).first()

    if show is None:
        response = _('Specified series is not on my list.')
    else:
        if chat is None:
            response = _('You are not subscribed to any of the series.')
        else:
            subs = shared.session.query(Subscription).filter(
                Subscription.show.mongo_id == show.mongo_id,
                Subscription.chat.mongo_id == chat.mongo_id).first()
            if not subs is None:
                shared.session.remove(subs)
                response = _('You have unsubscribed from the show.')
            else:
                response = _('You are not subscribed to the show.')

    bot.sendMessage(chat_id=update.message.chat_id, text=response)


def subscriptions(bot, update):
    ''' Returns active subscriptions of the chat. '''

    chat = shared.session.query(Chat).filter(
        Chat.id == update.message.chat_id).first()

    if chat is None:
        response = _('You are not subscribed to any of the series.')
    else:
        subslist = list(shared.session.query(Subscription).filter(
            Subscription.chat.mongo_id == chat.mongo_id))
        if not len(subslist):
            response = _('You are not subscribed to any of the series.')
        else:
            response = '\n'.join([
                _('List of active subscriptions:') + '\n'
            ] + [' '.join([
                Emoji.BLACK_SMALL_SQUARE,
                s.show.title.encode('utf8')]) for s in subslist])

    bot.sendMessage(chat_id=update.message.chat_id, text=response)
