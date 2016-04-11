import re
import __builtin__ as shared

from telegram import Emoji, ReplyKeyboardMarkup, ReplyKeyboardHide
from models import Chat, Subscription, Show, Season, Episode


__all__ = [
    'start',
    'showlist',
    'subscribe',
    'unsubscribe',
    'subscriptions',
    'setlang',
    'watch',
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


def watch(bot, update):
    ''' Returns an embedded video of episodes. '''

    chat = get_chat(update.message.chat_id)
    request = update.message.text[7:].strip().lower()

    try:

        if not len(request):
            chat.ref = 'watch__'
            shared.session.update(chat)
            response = _('Which TV show would you like to see?')
            bot.sendMessage(chat_id=update.message.chat_id,
                            text=response,
                            reply_markup=ReplyKeyboardHide())
        else:
            matches = (re.search(r'^(.+)_(\d+)$', request, re.U),
                       re.search(r'^(.+)_(\d+)_(\d+)$', request, re.U))

            show_title, season_number, episode_number = None, None, None
            if not matches[1] is None:
                show_title = matches[1].group(1)
                season_number = int(matches[1].group(2))
                episode_number = int(matches[1].group(3))
            elif not matches[0] is None:
                show_title = matches[0].group(1)
                season_number = int(matches[0].group(2))
            else:
                show_title = request

            show = shared.session.query(Show).filter(Show.title_lower == show_title).first()
            if show is None:
                response = _('Specified series is not on my list.')
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=response,
                                reply_markup=ReplyKeyboardHide())
                chat.ref = ''
                shared.session.update(chat)
                return
            elif not shared.session.query(Episode).filter(
                Episode.season.show.mongo_id == show.mongo_id, Episode.url != '').count():

                response = _('Unfortunately, we do not have any series of this TV show.')
                bot.sendMessage(chat_id=update.message.chat_id,
                                text=response,
                                reply_markup=ReplyKeyboardHide())
                chat.ref = ''
                shared.session.update(chat)
                return

            if season_number is None:
                chat.ref = 'watch__%s' % show_title
                shared.session.update(chat)
                response = _('Which season would you like to see?')

                seasons, buttons = shared.session.query(Season).filter(
                    Season.show.mongo_id == show.mongo_id), []

                for season in seasons:
                    if shared.session.query(Episode).filter(
                        Episode.season.mongo_id == season.mongo_id,
                        Episode.url != '').count():
                        buttons.append(str(season.number))

                buttons = sorted(list(set(buttons)), key=lambda x: int(x))
                buttons = [buttons[i:i+3] for i in xrange(0, len(buttons), 3)]

                bot.sendMessage(chat_id=update.message.chat_id,
                                text=response,
                                reply_markup=ReplyKeyboardMarkup(buttons))
                return
            else:
                season = shared.session.query(Season).filter(
                    Season.show.mongo_id == show.mongo_id, Season.number == season_number).first()

                if season is None:
                    response = _('Wrong season.')
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=response,
                                    reply_markup=ReplyKeyboardHide())
                    return
                elif not shared.session.query(Episode).filter(
                    Episode.season.show.mongo_id == show.mongo_id,
                    Episode.season.number == season_number,
                    Episode.url != '').count():

                    response = _('Unfortunately, we do not have any series of this season.')
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=response,
                                    reply_markup=ReplyKeyboardHide())
                    chat.ref = ''
                    shared.session.update(chat)
                    return

            if episode_number is None:
                chat.ref = 'watch__%s_%d' % (show_title, season_number)
                shared.session.update(chat)
                response = _('Which episode would you like to see?')

                episodes = shared.session.query(Episode).filter(
                    Episode.season.mongo_id == season.mongo_id, Episode.url != '')

                buttons = sorted(list(set([str(ep.number) for ep in episodes])), key=lambda x: int(x))
                buttons = [buttons[i:i+3] for i in xrange(0, len(buttons), 3)]

                bot.sendMessage(chat_id=update.message.chat_id,
                                text=response,
                                reply_markup=ReplyKeyboardMarkup(buttons))
            else:
                episode = shared.session.query(Episode).filter(
                    Episode.season.mongo_id == season.mongo_id,
                    Episode.number == episode_number, Episode.url != '').first()

                if episode is None:
                    response = _('Wrong episode.')
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=response,
                                    reply_markup=ReplyKeyboardHide())
                    chat.ref = ''
                    shared.session.update(chat)
                else:
                    response = episode.url
                    bot.sendMessage(chat_id=update.message.chat_id,
                                    text=response,
                                    reply_markup=ReplyKeyboardHide())
                    chat.ref = ''
                    shared.session.update(chat)

    except Exception as e:
        print e

    return


def default(bot, update):

    chat = get_chat(update.message.chat_id)

    if chat.ref == 'subscribe':
        update.message.text, chat.ref = '/subscribe ' + update.message.text, ''
        subscribe(bot, update)
    elif chat.ref == 'unsubscribe':
        update.message.text, chat.ref = '/unsubscribe ' + update.message.text, ''
        unsubscribe(bot, update)
        shared.session.update(chat)
    elif chat.ref == 'setlang':
        update.message.text, chat.ref = '/setlang ' + update.message.text, ''
        setlang(bot, update)
        shared.session.update(chat)
    elif chat.ref.split('__')[0] == 'watch':
        if len(chat.ref.split('__')[1]):
            update.message.text = '/watch %s_%s' % (chat.ref.split('__')[1],
                                                    update.message.text)
        else:
            update.message.text = '/watch %s' % update.message.text
        watch(bot, update)
    else:
        start(bot, update)
