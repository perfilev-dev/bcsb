# coding: utf8

import __builtin__ as shared

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from bs4 import BeautifulSoup
import requests
import json

from util import configure_from_file
shared.config = configure_from_file('default.cfg')

from model import Show, Season, Episode
import neomodel
import datetime

import argparse


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
        date = filter(None, date)

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

    # Обрабатываем отсутствие результатов поиска
    try:
        episodes, number_of_seasones, serial_title = parse_toramp(title)
    except ValueError as e:
        print '{} для {}'.format(e.message, title)
        return

    # Если сериал существует - работаем с ним
    try:
        show = Show.nodes.get(title_lower=serial_title.lower())
    except neomodel.DoesNotExist:
        show = Show(title=unicode(serial_title)).save()

    for i in xrange(number_of_seasones):

        # Если сезон уже существует - работаем с ним
        try:
            season = show.seasons.get(number=i+1)
        except neomodel.DoesNotExist:
            season = Season(show=show, number=i+1).save()
            show.seasons.connect(season)

        episodes_in_season = filter(lambda x: x['season'] == i + 1, episodes)

        for element in episodes_in_season:

            # Если эпизод уже есть - пропускаем
            try:
                episode = season.episodes.get(
                    number=element['number'],
                    title=element['title'],
                    release_date=element['release']
                )

            except neomodel.DoesNotExist:
                episode = Episode(
                    season=season,
                    title=unicode(element['title']),
                    release_date=element['release'],
                    number=element['number'],
                    link_to_video=''
                ).save()
                season.episodes.connect(episode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', default='', type=str)
    args = parser.parse_args()

    if args.add:
        print 'adding ' + args.add
        add_or_update_show(args.add)
