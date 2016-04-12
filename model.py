import __builtin__ as shared

from neomodel import (StructuredNode, StringProperty, IntegerProperty, db,
                      DateTimeProperty, RelationshipTo, RelationshipFrom, One,
                      ZeroOrMore, DoesNotExist)


class Chat(StructuredNode):

    # telegram chat ID
    id = IntegerProperty(unique_index=True, required=True)

    # preferred language
    language = StringProperty(default='en')

    # traverse outgoing IS_SUBSCRIBED_FOR relation, inflate to Show objects
    subscriptions = RelationshipTo('Show', 'IS_SUBSCRIBED_FOR')

    @staticmethod
    def get_or_create(id):
        ''' Returns an object, creating it if necessary. '''

        try:
            chat = Chat.nodes.get(id=id)
        except DoesNotExist:
            chat = Chat(id=id).save()

        # Set the language of the responses
        shared.translations[chat.language].install()

        return chat


class Show(StructuredNode):
    def __init__(self, *args, **kwargs):

        # leads to lower case title
        if 'title' in kwargs:
            kwargs['title_lower'] = kwargs['title'].lower()

        try:
            super(Show, self).__init__(*args, **kwargs)
        except:
            pass

    title = StringProperty(required=True)
    title_lower = StringProperty(unique_index=True, required=True)

    # traverse incoming IS_SUBSCRIBED_FOR relation, inflate to Person objects
    subscribers = RelationshipFrom('Chat', 'IS_SUBSCRIBED_FOR')

    # traverse outgoing HAS relation, inflate to Season objects
    seasons = RelationshipTo('Season', 'HAS')

    @property
    def available_seasons(self):
        return [s for s in self.seasons.all()
                if len(s.episodes.search(link_to_video__ne=''))]

    @property
    def unavailable_seasons(self):
        return [s for s in self.seasons.all()
                if not len(s.episodes.search(link_to_video__ne=''))]


class Season(StructuredNode):
    def __init__(self, *args, **kwargs):

        # creates a unique index
        if 'show' in kwargs:
            kwargs['id'] = '%s s%d' % (kwargs['show'].title_lower, kwargs['number'])
            del kwargs['show']

        try:
            super(Season, self).__init__(*args, **kwargs)
        except:
            pass

    # serial number of season
    number = IntegerProperty(required=True)

    # identifier for indexing
    id = StringProperty(unique_index=True, required=True)

    # traverse incoming HAS relation, inflate to Show objects
    show = RelationshipFrom('Show', 'HAS', cardinality=One)

    # traverse outgoing HAS relation, inflate to Episode objects
    episodes = RelationshipTo('Episode', 'HAS')

    @property
    def available_episodes(self):
        return [ep for ep in self.episodes.all() if ep.is_available]

    @property
    def unavailable_episodes(self):
        return [ep for ep in self.episodes.all() if not ep.is_available]


class Episode(StructuredNode):
    def __init__(self, *args, **kwargs):

        # creates a unique index
        if 'season' in kwargs:
            kwargs['id'] = '%s e%d' % (kwargs['season'].id, kwargs['number'])
            del kwargs['season']

        try:
            super(Episode, self).__init__(*args, **kwargs)
        except:
            pass

    # serial number of series
    number = IntegerProperty(required=True)

    # identifier for indexing
    id = StringProperty(unique_index=True, required=True)

    title = StringProperty()

    release_date = DateTimeProperty()

    link_to_video = StringProperty()

    # traverse incoming HAS relation, inflate to Season objects
    season = RelationshipFrom('Season', 'HAS', cardinality=One)

    @property
    def show(self):
        return self.season.get().show

    @property
    def is_available(self):
        return not self.link_to_video in ['', None]
