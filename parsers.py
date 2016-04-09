# coding: utf8

import __builtin__ as shared

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from mongoalchemy.session import Session
from bs4 import BeautifulSoup
import requests

from models import Show, Season, Episode
import datetime

MONTHS = [
    u'января',
    u'февраля',
    u'марта',
    u'апреля',
    u'мая',
    u'июня',
    u'июля',
    u'августа',
    u'сентября',
    u'октября',
    u'ноября',
    u'декабря'
]

from utils.config import configure_from_file
shared.config = configure_from_file('default.cfg')

def parse_toramp(title):

    site_url = 'http://www.toramp.com/'

    # Получаем результат поиска
    search_url = site_url + 'search.php?search={}'.format(title)
    soup = BeautifulSoup(requests.get(search_url).text, 'html.parser')

    serials = soup.select('.title')

    if serials:
        serial_url = site_url + serials[0].attrs['href']
        serial_title = serials[0].text
    # Если поиск не выдал ничего
    else:
        raise ValueError('Не найдено')

    # Парсим страницу сериала
    soup = BeautifulSoup(requests.get(serial_url).text, 'html.parser')
    number_of_seasones = int(soup.select('.season-list a')[-1].text)

    release_time = 0

    # Если сериал закрыт, времени релиза нет - оставляем 0
    if soup.select('.content-widget-1 .block_bold')[-1].text == u'выходит в эфир':
        release_time = soup.select('.content-widget-1 .block_list')[-1].text
        release_time = int(release_time.split(' ')[1].split(':')[0])

    episodes = []

    # Парсим каждый эпизод и формируем список
    for element in soup.select('#full-season tr'):
        season, number = element.select('.number-of-episodes a')[0]['name'].split('x')
        title = element.select('.title-of-episodes b')[0].text
        date = element.select('.air-date span')[0].text.split(' ')

        # Если дата указана не полностью - пропускаем серию
        if len(date) < 3:
            continue

        day = int(date[0])
        month = MONTHS.index(date[1]) + 1
        year = int(date[2])

        release = datetime.datetime(year, month, day, release_time)

        record = {
            'season': int(season),
            'number': int(number),
            'title': title,
            'release': release
        }

        episodes.append(record)

    return episodes, number_of_seasones, serial_title

def add_or_update_show(title):

    shared.session = Session.connect(shared.config['database']['name'])

    # Обрабатываем отсутствие результатов поиска
    try:
        episodes, number_of_seasones, serial_title = parse_toramp(title)
    except ValueError as e:
        print '{} для {}'.format(e.message, title)
        return

    # Если сериал существует - работаем с ним
    show = session.query(Show).filter(Show.title == unicode(serial_title)).first()
    if not show:
        show = Show(title=unicode(serial_title))
        shared.session.save(show)

    for i in xrange(number_of_seasones):

        # Если сезон уже существует - работаем с ним
        season = session.query(Season).filter(
            Season.show.title == show.title and
            Season.number == i + 1
        ).first()
        if not season:
            season = Season(show=show, number=i+1)
            shared.session.save(season)

        episodes_in_season = filter(lambda x: x['season'] == i + 1, episodes)

        for element in episodes_in_season:

            # Если эпизод уже есть - пропускаем
            episode = session.query(Episode).filter(
                Episode.season == season and
                Episode.number == element['number'] and
                Episode.title == element['title'] and
                Episode.release == element['release']
            ).first()

            if not episode:
                episode = Episode(
                    season=season,
                    title=unicode(element['title']),
                    release=element['release'],
                    number=element['number'],
                    url=''
                )
                shared.session.save(episode)
