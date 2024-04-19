import click
from db.models import Article, Collection
from upload.full import upload_articles

# @click.group()
# def upload():
#     pass


@click.command()
@click.argument("collection", type=str)
def upload(collection):
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
