from peewee import *
from settings.settings import settings
import datetime
import uuid as uuid_pkg

db_obj = SqliteDatabase(settings.SQLITE_DB_FILE)


class BaseModel(Model):
    class Meta:
        database = db_obj


class Action(BaseModel):
    id = UUIDField(primary_key=True, default=uuid_pkg.uuid4)
    action_type = TextField()  # create, manage, upload
    created_at = DateTimeField(default=datetime.datetime.utcnow())
    # is_deleted = BooleanField(default=False)
    settings = TextField()

    title_used_tokens = IntegerField(null=True)


class Article(BaseModel):
    id = UUIDField(primary_key=True, default=uuid_pkg.uuid4)
    action = ForeignKeyField(Action)
    article_type = TextField()

    title = TextField(unique=True)
    url_ending = TextField(unique=True)
    outline_json = TextField(null=True)
    # tags_json = TextField(null=True)
    category = TextField(null=True)
    interlinking_uuids_json = TextField(null=True)
    sections_list_json = TextField(null=True)
    # faq_json = TextField(null=True)
    excerpt = TextField(null=True)
    image_description = TextField(null=True)
    image_generated = BooleanField(null=True)

    outline_tokens_used = IntegerField(null=True)
    sections_tokens_used = IntegerField(null=True)

    is_complete = BooleanField(default=False)
    is_succesful = BooleanField(null=True)
    is_published = BooleanField(default=False)
    # article_deleted = BooleanField(default=False)

    # full_article_markdown = TextField(null=True)
    # html_converted_markdown = TextField(null=True)


class Categorie(BaseModel):
    id = UUIDField(primary_key=True, default=uuid_pkg.uuid4)
    term = TextField(unique=True)


class ArticleLink(BaseModel):
    id = UUIDField(primary_key=True, default=uuid_pkg.uuid4)
    from_article = ForeignKeyField(Article)
    to_article = ForeignKeyField(Article)
