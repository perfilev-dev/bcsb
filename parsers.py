# coding: utf8

import __builtin__ as shared

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from mongoalchemy.session import Session
from bs4 import BeautifulSoup
import requests
import json

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


def get_episode_url(episode):

    episode_number = episode.number
    episode_title = unicode(episode.title.lower())
    season_number = episode.season.number
    show_title = unicode(episode.season.show.title.lower())

    vk_token = shared.config['vk']['token']

    GET_VIDEOS_TMPL = u'https://api.vk.com/method/video.search?q={0}&sort=0&access_token={1}&v=5.50&longer={2}&count=200'

    episode_name = u'{} сезон {} серия {}'.format(show_title, season_number, episode_number)
    query = GET_VIDEOS_TMPL.format(episode_name, vk_token, 600)

    requests.packages.urllib3.disable_warnings()
    response = requests.get(query).text
    response_json = json.loads(response)

    if 'error' in response_json:
        code = response_json['error']['error_code']
        message = response_json['error']['error_msg']
        print code, message

    result = response_json['response']['items']

    def filter_videos(list_of_videos, show_name, season_number, episode_number, episode_title):

        result = []

        for element in list_of_videos:

            element_title = element['title'].lower()
            element_description = element['description'].lower()
            # Если название сериала нет в title - пропускаем
            if show_name not in element_title:
                continue

            # Проверяем title
            if u'сезон {} '.format(season_number) in element_title and u'серия {}'.format(episode_number) in element_title:
                # Если мы искали серию 2, а получили 21 - пропускаем
                next_index = element_title.find(u'серия {}'.format(episode_number)) + len(u'серия {}'.format(episode_number))
                if len(element_title) > next_index and element_title[next_index] in '0123456789':
                    continue
                result.append(element)
                continue

            # Проверяем title
            if u' {} сезон'.format(season_number) in element_title and u' {} серия'.format(episode_number) in element_title:
                result.append(element)
                continue

            # Проверяем title
            if episode_title in element_title:
                result.append(element)
                continue

            # Проверяем description
            if u'сезон {} '.format(season_number) in element_description and u'серия {}'.format(episode_number) in element_description:
                # Если мы искали серию 2, а получили 21 - пропускаем
                next_index = element_description.find(u'серия {}'.format(episode_number)) + len(u'серия {}'.format(episode_number))
                if len(element_description) > next_index and element_description[next_index] in '0123456789':
                    continue
                result.append(element)
                continue

            # Проверяем description
            if u' {} сезон'.format(season_number) in element_description and u' {} серия'.format(episode_number) in element_description:
                result.append(element)
                continue

            # Наличие названия серии в description
            if episode_title in element_description:
                result.append(element)
                continue

        return sorted(result, key=lambda x: x['views'], reverse=True)

    result = filter_videos(result, show_title, season_number, episode_number, episode_title)

    for element in result:
        if 'vk.com' in element['player']:
            oid = element['player'].split('oid=')[1].split('&')[0]
            vk_id = element['player'].split('&id=')[1].split('&')[0]
            if not requests.get('http://vk.com/video{}_{}'.format(oid, vk_id)).status_code == 403:
                return 'http://vk.com/video{}_{}'.format(oid, vk_id)


def update_episode_url(episode):
    shared.session = Session.connect(shared.config['database']['name'])
    url = get_episode_url(episode)

    if url and url != episode.url:
        episode.url = url
        session.save(episode)
