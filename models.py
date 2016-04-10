from mongoalchemy.document import Document, Index
from mongoalchemy.fields import *


class Chat(Document):
    config_collection_name = 'chats'

    id = IntField(min_value=0)
    lang = EnumField(StringField(), 'en', 'ru')
    ref = StringField()


class Show(Document):
    config_collection_name = 'shows'

    title = StringField()

    @computed_field(StringField(), deps=[title])
    def title_lower(obj):
        return obj.get('title','').lower()

    t_index = Index().ascending('title').unique()


class Season(Document):
    config_collection_name = 'seasones'

    show = DocumentField(Show)
    number = IntField(min_value=0)


class Episode(Document):
    config_collection_name = 'episodes'

    title = StringField()
    number = IntField(min_value=0)
    season = DocumentField(Season)
    release = DateTimeField()
    url = StringField(required=False)


class Subscription(Document):
    config_collection_name = 'subscriptions'

    chat = DocumentField(Chat)
    show = DocumentField(Show)
