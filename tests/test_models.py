import sys
import unittest
import __builtin__ as shared

from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from datetime import datetime
from mongoalchemy.session import Session
from utils.config import configure_for_unittest
from pymongo.errors import DuplicateKeyError


class TestChat(unittest.TestCase):

    def test_existence(self):
        from models import Chat

    def test_create(self):
        from models import Chat

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        chat = Chat(id=1)

        try:
            shared.session.save(chat)
        except Exception as e:
            del shared.session
            self.fail(e)
        del shared.session


class TestShow(unittest.TestCase):

    def test_existence(self):
        from models import Show

    def test_create(self):
        from models import Show

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        show = Show(title='House of Cards')

        try:
            shared.session.save(show)
        except Exception as e:
            del shared.session
            self.fail(e)
        del shared.session

    def test_remove(self):
        from models import Show, Season, Episode

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        show = Show(title='House of Cards')
        season = Season(show=show, number=1)
        shared.session.save(show)
        shared.session.save(season)
        del show, season

        show = shared.session.query(Show).filter(Show.title == 'House of Cards').first()
        for season in list(shared.session.query(Season).filter(Season.show.mongo_id == show.mongo_id)):
            for episode in list(shared.session.query(Episode).filter(Episode.season.mongo_id == season.mongo_id)):
                shared.session.remove(episode)
            shared.session.remove(season)
        shared.session.remove(show)

        counts = (shared.session.query(Show).count(),
                  shared.session.query(Season).count())
        del shared.session

        self.assertEqual(0, sum(counts))

    def test_duplicate(self):
        from models import Show

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        show1 = Show(title='House of Cards')
        show2 = Show(title='House of Cards')

        shared.session.save(show1)

        with self.assertRaises(DuplicateKeyError):
            shared.session.save(show2)


class TestSeason(unittest.TestCase):

    def test_existence(self):
        from models import Season

    def test_create(self):
        from models import Show, Season

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        show = Show(title='House of Cards')
        shared.session.save(show)

        season = Season(show=show, number=1)
        try:
            shared.session.save(season)
        except Exception as e:
            del shared.session
            self.fail(e)
        del shared.session

    def test_remove(self):
        from models import Show, Season, Episode

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        show = Show(title='House of Cards')
        season = Season(show=show, number=1)
        episode = Episode(title='Chapter 1',
                          number=1,
                          season=season,
                          release=datetime(2013,1,1))
        shared.session.save(show)
        shared.session.save(season)
        del show, season, episode

        season = shared.session.query(Season).filter(Season.show.title == 'House of Cards',
                                                     Season.number == 1).first()
        for episode in list(shared.session.query(Episode).filter(Episode.season.mongo_id == season.mongo_id)):
            shared.session.remove(episode)
        shared.session.remove(season)

        counts = (shared.session.query(Season).count(),
                  shared.session.query(Episode).count())
        del shared.session

        self.assertEqual(0, sum(counts))


class TestEpisode(unittest.TestCase):

    def test_existence(self):
        from models import Episode


class TestSubscription(unittest.TestCase):

    def test_existence(self):
        from models import Subscription

    def test_create(self):
        from models import Show, Chat, Subscription

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        chat = Chat(id=1)
        show = Show(title='House of Cards')
        shared.session.save(show)
        shared.session.save(chat)
        del chat, show

        show = shared.session.query(Show).filter(Show.title == 'House of Cards').first()
        chat = shared.session.query(Chat).filter(Chat.id == 1).first()
        subs = Subscription(chat=chat, show=show)

        try:
            shared.session.save(subs)
        except Exception as e:
            del shared.session
            self.fail(e)
        del shared.session

    def test_remove(self):
        from models import Show, Chat, Subscription

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'],
                                         safe=True)

        chat = Chat(id=1)
        show = Show(title='House of Cards')
        subs = Subscription(chat=chat, show=show)
        shared.session.save(show)
        shared.session.save(chat)
        shared.session.save(subs)
        del chat, show, subs

        subs = shared.session.query(Subscription).filter(Subscription.chat.id==1,
                                                         Subscription.show.title=='House of Cards').first()
        shared.session.remove(subs)

        count = shared.session.query(Subscription).count()
        del shared.session

        self.assertEqual(0, count)


if __name__ == '__main__':
    unittest.main()
