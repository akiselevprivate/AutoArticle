import click
from settings.settings import settings
from db.models import Article
from settings.logger import logger
from utils.upload import upload_article, create_session, create_categorie_request
from generation.utils import generate_slug
import json

# @click.group()
# def upload():
#     pass


@click.command()
@click.argument("actions", type=str)
def upload(actions):
    if actions == "all":
        articles = Article.select().where(
            Article.is_complete,
            Article.is_published == False,
        )
        categories_db = (
            Article.select(Article.category)
            .where(
                Article.is_complete,
                Article.is_published == False,
            )
            .distinct()
        )
    elif actions == "reupload":
        articles = Article.select().where(
            Article.is_complete,
            Article.is_published,
        )
        categories_db = (
            Article.select(Article.category)
            .where(
                Article.is_complete,
                Article.is_published,
            )
            .distinct()
        )
    else:
        raise Exception("invalid")

    logger.info(f"Uploading {len(articles)} articles to {settings.SITE_URL}")

    session = create_session()

    categorie_dict = {}

    categories = [value[0] for value in categories_db.tuples()]

    for cat in categories:
        cat_data = dict(
            slug=generate_slug(cat),
            name=cat,
        )
        responce, success, categorie_id = create_categorie_request(session, cat_data)
        if not success:
            logger.error(responce.json())
            raise Exception("failed creating categorie")
        categorie_dict[cat] = categorie_id

    logger.info(f"Uploaded {len(categories)} categories")

    uploaded_articles = []
    for idx, article in enumerate(articles):
        # try:
        uploaded_article, success = upload_article(article, session, categorie_dict)

        uploaded_articles.append(uploaded_article)
        logger.info(
            f"successfully uploaded article: {uploaded_article.title}, ({idx+1}/{len(articles)})"
        )
        # except Exception as e:
        #     logger.error(e)
        #     logger.error(f"failed to upload article: {article.title}")

    logger.info(
        f"successfully uploaded {len(uploaded_articles)}/{len(articles)} articles"
    )
