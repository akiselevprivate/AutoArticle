import click
from db.models import Article, Collection
from upload.full import upload_articles
from datetime import datetime, timedelta
import random
from peewee import fn
from settings.settings import settings


@click.group()
def upload():
    pass


@upload.command()
@click.argument("collection", type=str)
def collection(collection):
    input(f"Are you sure you want to upload to {settings.SITE_URL}")
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
@click.argument("start-collection", type=str)
@click.argument("date", type=str)
def schedule(start_collection, date):
    input(f"Are you sure you want to upload to {settings.SITE_URL}")

    date_object = datetime.strptime(date, "%Y-%m-%d")

    if start_collection == "all":
        start_collection = 0

    collections: list[Collection] = (
        Collection.select()
        .where(Collection.id >= int(start_collection))
        .order_by(Collection.id.asc())
    )

    for idx, col in enumerate(collections):
        date_with_time = (date_object + timedelta(days=idx)).replace(
            hour=random.randint(0, 23), minute=random.randint(0, 59), second=0
        )

        articles = Article.select().where(Article.collection == col)

        formatted_date = date_with_time.strftime("%Y-%m-%d %H:%M:%S")
        upload_articles(articles, date=formatted_date)

        col.is_published = True
        col.save()


@upload.command()
@click.argument("collection", type=str)
@click.argument("date", type=str)
@click.argument("date2", type=str)
def shuffle(collection, date, date2):
    input(f"Are you sure you want to upload to {settings.SITE_URL}")

    date_obj = datetime.strptime(date, "%Y-%m-%d")
    date2_obj = datetime.strptime(date2, "%Y-%m-%d")

    days = abs(date_obj - date2_obj).days

    collection = Collection.get_or_none(id=collection)
    if not collection:
        raise Exception("Collection does not exist")

    articles: list[Article] = (
        Article.select().where(Article.collection == collection).order_by(fn.Random())
    )

    article_ids = [a.id for a in articles]

    def batch(input_list: list, n: int):
        # Calculate the size of each batch
        batch_size = len(input_list) // n
        # Initialize the list of batches
        batches = []
        # Split the input list into batches
        for i in range(0, len(input_list), batch_size):
            batches.append(input_list[i : i + batch_size])
        return batches

    batches = batch(article_ids, days)

    for idx, ids in enumerate(batches):
        date_with_time = (date_obj + timedelta(days=idx)).replace(
            hour=random.randint(0, 23), minute=random.randint(0, 59), second=0
        )

        upload_as = Article.select().where(Article.id << ids)

        formatted_date = date_with_time.strftime("%Y-%m-%d %H:%M:%S")
        upload_articles(upload_as, date=formatted_date)

    collection.is_published = True
    collection.save()
