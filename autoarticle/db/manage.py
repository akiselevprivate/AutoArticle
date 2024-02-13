from peewee import SqliteDatabase
from db.models import *


def create_db(db: SqliteDatabase):
    db.create_tables([Action, Article, ArticleLink, Categorie])
