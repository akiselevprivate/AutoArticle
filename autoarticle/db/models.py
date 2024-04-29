from peewee import *
from settings.settings import settings
import datetime
import uuid as uuid_pkg
import json

db_obj = SqliteDatabase(settings.SQLITE_DB_FILE)


class BaseModel(Model):
    class Meta:
        database = db_obj


class JSONField(TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


uuid_fn = lambda: str(uuid_pkg.uuid4())


class Collection(BaseModel):
    is_complete = BooleanField(default=False)
    is_published = BooleanField(default=False)


class Article(BaseModel):
    id = TextField(primary_key=True, default=uuid_fn)
    # article_type = TextField()

    collection = ForeignKeyField(Collection)

    topic = TextField()
    category = TextField()

    article_type = TextField()
    content_type = TextField()
    tone = TextField()
    data_req = BooleanField()
    image_req = BooleanField()

    title = TextField(unique=True)
    slug = TextField(unique=True)

    excerpt = TextField(null=True)

    additional_data = TextField(null=True)
    additional_data_split = BooleanField(default=False)

    embedding_complete = BooleanField(default=False)

    outline_generated = BooleanField(default=False)
    interlinking_uuids_generated = BooleanField(default=False)

    additional_anchors = JSONField(default=[])

    faq = JSONField(null=True)

    image_description = TextField(null=True)
    image_id = TextField(null=True)

    video_query = TextField(null=True)
    youtube_embed_url = TextField(null=True)

    is_complete = BooleanField(default=False)
    is_published = BooleanField(default=False)


class Product(BaseModel):

    article = ForeignKeyField(Article)

    full_name = TextField()
    description = TextField()
    reviews = JSONField()
    rating = FloatField()
    price = FloatField()
    image_url = TextField()
    url = TextField()
    source_name = TextField()

    is_generated = BooleanField(default=False)

    pros = JSONField(null=True)
    cons = JSONField(null=True)
    short_name = TextField(null=True)
    summary = TextField(null=True)


class Section(BaseModel):
    id = TextField(primary_key=True, default=uuid_fn)

    article = ForeignKeyField(Article)

    title = TextField()
    idx = IntegerField()
    include_link = BooleanField()
    include_image = BooleanField()

    image_description = TextField(null=True)
    image_id = TextField(null=True)

    product = ForeignKeyField(Product, null=True)

    additional_data = TextField(null=True)

    # embedding =
    markdown = TextField(null=True)
    link = ForeignKeyField(Article, null=True)
    anchor = TextField(null=True)

    generated_anchor = TextField(null=True)
    word_count = IntegerField(null=True)
