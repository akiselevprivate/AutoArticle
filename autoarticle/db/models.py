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
    is_deleted = BooleanField(default=False)
    settings = TextField()

    title_used_tokens = IntegerField(null=True)
    alt_titles_used_tokens = IntegerField(null=True)
    outline_used_tokens = IntegerField(null=True)
    sections_used_tokens = IntegerField(null=True)


class Article(BaseModel):
    id = UUIDField(primary_key=True, default=uuid_pkg.uuid4)
    action = ForeignKeyField(Action)
    article_type = TextField()

    title = TextField(unique=True)
    url_ending = TextField(unique=True)
    alternative_title = TextField()
    outline_json = TextField(null=True)
    tags_json = TextField(null=True)
    categories_json = TextField(null=True)
    sections_list_json = TextField(null=True)

    is_complete = BooleanField(default=False)
    is_succesful = BooleanField(null=True)
    is_published = BooleanField(default=False)

    full_article_markdown = TextField(null=True)


class ArticleLink(BaseModel):
    id = UUIDField(primary_key=True, default=uuid_pkg.uuid4)
    from_article = ForeignKeyField(Article)
    to_article = ForeignKeyField(Article)
