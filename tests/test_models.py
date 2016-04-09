import sys
import unittest
import __builtin__ as shared

from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from datetime import datetime
from mongoalchemy.session import Session
from utils.config import configure_for_unittest


class TestChat(unittest.TestCase):

    def test_existence(self):
        from models import Chat

    def test_create(self):
        from models import Chat

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'])

        chat = Chat(id=1, title='Sample Chat')

        try:
            shared.session.save(chat)
        except Exception as e:
            del shared.session
            self.fail(e)


class TestShow(unittest.TestCase):

    def test_existence(self):
        from models import Show

    def test_create(self):
        from models import Show

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'])

        show = Show(title='House of Cards')

        try:
            shared.session.save(show)
        except Exception as e:
            del shared.session
            self.fail(e)

    def test_remove(self):
        from models import Show, Season

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'])

        show = Show(title='House of Cards')
        season = Season(show=show, number=1)
        shared.session.save(season)
        del show, season

        show = shared.session.query(Show).first()        
        shared.session.remove(show)
        self.assertEqual(0, shared.session.query(Season).count())


class TestSeason(unittest.TestCase):

    def test_existence(self):
        from models import Season

    def test_create(self):
        from models import Show, Season

        shared.config = configure_for_unittest()
        shared.session = Session.connect(shared.config['database']['name'])

        show = Show(title='House of Cards')
        shared.session.save(show)

        season = Season(show=show, number=1)
        try:
            shared.session.save(season)
        except Exception as e:
            del shared.session
            self.fail(e)


class TestEpisode(unittest.TestCase):

    def test_existence(self):
        from models import Episode


class TestSubscription(unittest.TestCase):

    def test_existence(self):
        from models import Subscription


if __name__ == '__main__':
    unittest.main()
