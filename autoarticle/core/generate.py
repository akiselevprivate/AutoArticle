import click
from db.models import Collection, Article
from generation.parts import generate_articles
from settings.logger import logger
from settings.settings import settings


@click.command()
@click.argument("collection")
def generate(collection):
    if collection == "all":
        collections = Collection.select()
    else:
        collection_inst = Collection.get_or_none(id=collection)
        if not collection_inst:
            raise Exception("invalid collection id")
        collections: list[Collection] = [collection_inst]

    for idx, c in enumerate(collections, start=1):
        logger.info(f"Generating collection: {c.id}, ({idx}/{len(collections)})")
        articles = Article.select().where(Article.collection == c)
        generate_articles(articles, settings.GENERATE_IMAGE, settings.FAQ_AMOUNT)
        logger.info(
            f"Finished generating collection: {c.id}, ({idx}/{len(collections)})"
        )
        c.is_complete = True
        c.save()
