import click
from db.models import Article, Collection
from upload.full import upload_articles
from datetime import datetime, timedelta
import random


@click.group()
def upload():
    pass


@upload.command()
@click.argument("collection", type=str)
def collection(collection):
    if collection == "all":
        collections: list[Collection] = Collection.select().where(
            Collection.is_published == False
        )
    elif collection == "reupload":
        collections: list[Collection] = Collection.select().where(
            Collection.is_published == True
        )
    else:
        collection_inst = Collection.get_or_none(id=collection)
        if not collection_inst:
            raise Exception("Collection doesent exist")
        collections = [collection_inst]

    articles = Article.select().where(Article.collection << collections)

    upload_articles(articles)

    for col in collections:
        col.is_published = True
        col.save()


@upload.command()
@click.argument("date", type=str)
def schedule(date):
    date_object = datetime.strptime(date, "%Y-%m-%d")

    collections: list[Collection] = Collection.select().order_by(Collection.id.asc())

    for idx, col in enumerate(collections):
        date_with_time = (date_object + timedelta(days=idx)).replace(
            hour=random.randint(0, 24), minute=random.randint(0, 60), second=0
        )

        articles = Article.select().where(Article.collection == col)

        formatted_date = date_with_time.strftime("%Y-%m-%d %H:%M:%S")
        upload_articles(articles, date=formatted_date)

        col.is_published = True
        col.save()
