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


class Article(BaseModel):
    id = TextField(primary_key=True, default=uuid_fn)
    # article_type = TextField()

    title = TextField(unique=True)
    slug = TextField(unique=True)
    category = TextField()

    excerpt = TextField(null=True)

    additional_data = TextField(null=True)
    additional_data_split = BooleanField(default=False)

    embedding_complete = BooleanField(default=False)

    outline_generated = BooleanField(default=False)
    interlinking_uuids_generated = BooleanField(default=False)

    additional_anchors = JSONField(default=[])

    image_description = TextField(null=True)
    image_id = TextField(null=True)

    youtube_embed_url = TextField(null=True)

    is_complete = BooleanField(default=False)
    is_published = BooleanField(default=False)


class Section(BaseModel):

    article = ForeignKeyField(Article)

    title = TextField()
    idx = IntegerField()
    include_link = BooleanField()
    include_image = BooleanField()

    image_description = TextField(null=True)
    image_id = TextField(null=True)

    additional_data = TextField(null=True)

    # embedding =
    markdown = TextField(null=True)
    link = ForeignKeyField(Article, null=True)
    anchor = TextField(null=True)

    generated_anchor = TextField(null=True)
    word_count = IntegerField(null=True)
