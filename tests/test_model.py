import sys
import unittest

from os import path, environ
from datetime import datetime as dt

# Export dir for import module like from root directory
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from util import configure_for_unittest


class TestChat(unittest.TestCase):

    def test_nonexistent(self):
        ''' Tests raise exception with trying to access the non-existent object. '''

        configure_for_unittest()
        from model import Chat
        from neomodel import DoesNotExist

        with self.assertRaises(DoesNotExist):
            Chat.nodes.get(id=-1)

    def test_multiple_returned(self):
        ''' Tests raise exception with trying to access multiple returned objects
            with .get().
        '''

        configure_for_unittest()
        from model import Chat
        from neomodel import MultipleNodesReturned

        Chat(id=1).save()
        Chat(id=2).save()

        with self.assertRaises(MultipleNodesReturned):
            Chat.nodes.get(id__lt=10)

    def test_get_or_create(self):
        ''' Tests the creation of the object, if necessary. '''

        configure_for_unittest()
        from model import Chat

        Chat(id=1).save()

        chat1 = Chat.get_or_create(id=1)
        chat2 = Chat.get_or_create(id=2)


class TestShow(unittest.TestCase):

    def test_create_duplicates(self):
        ''' Tests raise exception with trying to create duplicates. '''

        configure_for_unittest()
        from model import Show
        from neomodel import UniqueProperty

        show1 = Show(title='House of Cards').save()
        show2 = Show(title='House of Cards')

        with self.assertRaises(UniqueProperty):
            show2.save()

    def test_nonexistent(self):
        ''' Tests raise exception with trying to access the non-existent object. '''

        configure_for_unittest()
        from model import Show
        from neomodel import DoesNotExist

        with self.assertRaises(DoesNotExist):
            Show.nodes.get(title_lower='nonexistent serial')

    def test_multiple_returned(self):
        ''' Tests raise exception with trying to access multiple returned objects
            with .get().
        '''

        configure_for_unittest()
        from model import Show
        from neomodel import MultipleNodesReturned

        Show(title='House of Cards').save()
        Show(title='Teacher Gym').save()

        with self.assertRaises(MultipleNodesReturned):
            Show.nodes.get(title__ne='Kitchen')

    def test_availability(self):
        ''' Tests availabity properties of object. '''

        configure_for_unittest()
        from model import Show, Season, Episode

        show = Show(title='House of Cards').save()
        season1 = Season(show=show, number=1).save()
        season2 = Season(show=show, number=2).save()
        episode1 = Episode(season=season1, number=1, release_date=dt(2010,1,1)).save()
        episode2 = Episode(season=season1, number=2).save()
        episode3 = Episode(season=season2, number=1).save()

        show.seasons.connect(season1)
        show.seasons.connect(season2)
        season1.episodes.connect(episode1)
        season1.episodes.connect(episode2)
        season2.episodes.connect(episode3)

        self.assertEqual(show.available_seasons[0], season1)
        self.assertEqual(show.unavailable_seasons[0], season2)


class TestSeason(unittest.TestCase):

    def test_availability(self):
        ''' Tests availabity properties of object. '''

        configure_for_unittest()
        from model import Show, Season, Episode

        show = Show(title='House of Cards').save()
        season1 = Season(show=show, number=1).save()
        season2 = Season(show=show, number=2).save()
        episode1 = Episode(season=season1, number=1, release_date=dt(2010,1,1)).save()
        episode2 = Episode(season=season1, number=2).save()

        show.seasons.connect(season1)
        show.seasons.connect(season2)
        season1.episodes.connect(episode1)
        season1.episodes.connect(episode2)

        self.assertEqual(season1.available_episodes[0], episode1)
        self.assertEqual(season1.unavailable_episodes[0], episode2)


class TestEpisode(unittest.TestCase):

    def test_availability(self):
        ''' Tests availabity properties of object. '''

        configure_for_unittest()
        from model import Show, Season, Episode

        show = Show(title='House of Cards').save()
        season1 = Season(show=show, number=1).save()
        season2 = Season(show=show, number=2).save()
        episode1 = Episode(season=season1, number=1, release_date=dt(2010,1,1)).save()
        episode2 = Episode(season=season1, number=2).save()
        episode3 = Episode(season=season2, number=1).save()

        show.seasons.connect(season1)
        show.seasons.connect(season2)
        season1.episodes.connect(episode1)
        season1.episodes.connect(episode2)
        season2.episodes.connect(episode3)

        self.assertTrue(episode1.is_available)
        self.assertFalse(episode2.is_available)


class TestVideo(unittest.TestCase):

    def test_create_duplicates(self):
        ''' Tests raise exception with trying to create duplicates. '''

        configure_for_unittest()
        from model import Video
        from neomodel import UniqueProperty

        video1 = Video(link='https://vk.com/blablabla').save()
        video2 = Video(link='vk.com/blablabla')

        with self.assertRaises(UniqueProperty):
            video2.save()

    def test_get_episode(self):
        ''' Tests getting episode from video's field. '''

        configure_for_unittest()
        from model import Video, Show, Season, Episode

        show = Show(title='House of Cards').save()
        season1 = Season(show=show, number=1).save()
        season2 = Season(show=show, number=2).save()
        episode1 = Episode(season=season1, number=1, release_date=dt(2010,1,1)).save()
        episode2 = Episode(season=season1, number=2).save()
        episode3 = Episode(season=season2, number=1).save()
        video = Video(link='vk.com').save()

        show.seasons.connect(season1)
        show.seasons.connect(season2)
        season1.episodes.connect(episode1)
        season1.episodes.connect(episode2)
        season2.episodes.connect(episode3)
        episode1.videos.connect(video)

        video.refresh()

        self.assertEqual(video.episode.get().number, 1)


if __name__ == '__main__':
    unittest.main()
