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

    embedding_complete = BooleanField(default=False)

    section_titles = JSONField(null=True)
    sections = JSONField(null=True)

    interlinking_uuids = JSONField(null=True)

    image_description = TextField(null=True)
    image_generated = BooleanField(default=False)

    outline_tokens_used = IntegerField(null=True)
    sections_tokens_used = IntegerField(null=True)

    is_complete = BooleanField(default=False)
    is_succesful = BooleanField(default=False)
    is_published = BooleanField(default=False)
    # article_deleted = BooleanField(default=False)

    # full_article_markdown = TextField(null=True)
    # html_converted_markdown = TextField(null=True)
