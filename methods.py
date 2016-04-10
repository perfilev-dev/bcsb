import __builtin__ as shared

from telegram import Emoji, ReplyKeyboardMarkup, ReplyKeyboardHide
from models import Show, Chat, Subscription


__all__ = [
    'start',
    'showlist',
    'subscribe',
    'unsubscribe',
    'subscriptions',
    'setlang',
    'default'
]


def get_chat(chat_id):
    ''' Finds the chat and creates one if needed. '''

    chat = shared.session.query(Chat).filter(Chat.id == chat_id).first()

    if chat is None:
        chat = Chat(id=chat_id, lang=shared.config['telegram']['lang'], ref='')
        shared.session.save(chat)

    shared.lang[chat.lang].install()
    return chat


def start(bot, update):
    ''' Mandatory method according to Telegram API. '''

    get_chat(update.message.chat_id)

    response = (
        _('You can control me by sending these commands:') + '\n',
        '/showlist - %s' % _('show list of available TV shows'),
        '/subscriptions - %s' % _('show active subscriptions'),
        '/subscribe - %s' % _('subscribe to a TV show'),
        '/unsubscribe - %s' % _('unsubscribe from a TV show'),
        '/setlang - %s' % _('change language')
    )

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(response),
                    reply_markup=ReplyKeyboardHide())


def showlist(bot, update):
    ''' Show the list of available TV shows. '''

    response = [ _('List of available TV shows:') + '\n' ]

    chat = get_chat(update.message.chat_id)
    titles = sorted([(x.mongo_id,
                      x.title.encode('utf8')) for x in shared.session.query(Show)],
                     key=lambda x: x[1])

    ids = [x.show.mongo_id for x in shared.session.query(Subscription).filter(
        Subscription.chat.mongo_id == chat.mongo_id)]

    response += [' '.join([
        Emoji.BLACK_SMALL_SQUARE if title[0] in ids else Emoji.WHITE_SMALL_SQUARE,
        title[1]
    ]) for title in titles]

    bot.sendMessage(chat_id=update.message.chat_id,
                    text='\n'.join(response),
                    reply_markup=ReplyKeyboardHide())


def subscribe(bot, update):
    ''' Subscribes chat on the show. '''

    title = update.message.text[11:].strip().lower()
    chat = get_chat(update.message.chat_id)

    if not len(title):
        chat.ref = 'subscribe'
        shared.session.update(chat)
        response = _('Which series would you like to subscribe?')
    else:
        show = shared.session.query(Show).filter(Show.title_lower == title).first()

        if show is None:
            response = _('Specified series is not on my list.')
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

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=ReplyKeyboardHide())


def unsubscribe(bot, update):
    ''' Unubscribes chat from the show. '''

    chat = get_chat(update.message.chat_id)
    title = update.message.text[13:].strip().lower()

    if not len(title):
        chat.ref = 'unsubscribe'
        shared.session.update(chat)
        response = _('Which series would you like to unsubscribe?')
    else:
        show = shared.session.query(Show).filter(Show.title_lower == title).first()

        if show is None:
            response = _('Specified series is not on my list.')
        else:
            subs = shared.session.query(Subscription).filter(
                Subscription.show.mongo_id == show.mongo_id,
                Subscription.chat.mongo_id == chat.mongo_id).first()
            if not subs is None:
                shared.session.remove(subs)
                response = _('You have unsubscribed from the show.')
            else:
                response = _('You are not subscribed to the show.')

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=ReplyKeyboardHide())


def subscriptions(bot, update):
    ''' Returns active subscriptions of the chat. '''

    chat = get_chat(update.message.chat_id)
    subslist = list(shared.session.query(Subscription).filter(
        Subscription.chat.mongo_id == chat.mongo_id))

    if not len(subslist):
        response = _('You are not subscribed to any of the series.')
    else:
        response = '\n'.join([_('List of active subscriptions:') + '\n'
        ] + [' '.join([Emoji.BLACK_SMALL_SQUARE,
                       s.show.title.encode('utf8')]) for s in subslist])

    bot.sendMessage(chat_id=update.message.chat_id,
                    text=response,
                    reply_markup=ReplyKeyboardHide())


def setlang(bot, update):
    ''' Changes language of responses. '''

    chat = get_chat(update.message.chat_id)
    lang = update.message.text[9:].strip().lower()

    new_lang = None
    if not len(lang):
        chat.ref = 'setlang'
        shared.session.update(chat)
        response = _('Which language do you prefer?')
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=response,
                        reply_markup=ReplyKeyboardMarkup([['en', 'ru']]))
    elif lang in ['en', 'english']:
        new_lang = 'en'
    elif lang in ['ru', 'russian']:
        new_lang = 'ru'
    else:
        response = _('Unknown language!')
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=response,
                        reply_markup=ReplyKeyboardHide())

    if not new_lang is None:
        if chat.lang != new_lang:
            chat.lang = new_lang
            shared.session.update(chat)
            chat = get_chat(update.message.chat_id)
            response = _('The language has changed!')
        else:
            response = _('You are already using this language!')
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=response,
                        reply_markup=ReplyKeyboardHide())


def default(bot, update):

    chat = get_chat(update.message.chat_id)

    if chat.ref == 'subscribe':
        update.message.text, chat.ref = '/subscribe ' + update.message.text, ''
        subscribe(bot, update)
        shared.session.update(chat)
    elif chat.ref == 'unsubscribe':
        update.message.text, chat.ref = '/unsubscribe ' + update.message.text, ''
        unsubscribe(bot, update)
        shared.session.update(chat)
    elif chat.ref == 'setlang':
        update.message.text, chat.ref = '/setlang ' + update.message.text, ''
        setlang(bot, update)
        shared.session.update(chat)
    else:
        start(bot, update)
