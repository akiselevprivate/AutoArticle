import click
from settings.settings import settings
from db.models import Action, Article
from settings.logger import logger
from utils.upload import upload_article, create_session
import json

# @click.group()
# def upload():
#     pass


@click.command()
@click.argument("actions", type=str)
def upload(actions):
    settings_dump = settings.model_dump()
    settings_dump["ACTIONS"] = actions
    action = Action.create(action_type="upload", settings=json.dumps(settings_dump))
    if actions == "all":
        articles = (
            Article.select()
            .join(Action)
            .where(
                Article.article_type == settings.ARTICLE_TYPE,
                Article.is_complete,
                Article.is_succesful,
                Article.is_published == False,
            )
        )
    elif actions == "reupload":
        articles = (
            Article.select()
            .join(Action)
            .where(
                Article.article_type == settings.ARTICLE_TYPE,
                Article.is_complete,
                Article.is_succesful,
                Article.is_published,
            )
        )
    else:
        articles = (
            Article.select()
            .join(Action)
            .where(
                Action.uuid == action,
                Article.article_type == settings.ARTICLE_TYPE,
                Article.is_complete,
                Article.is_succesful,
                Article.is_published == False,
            )
        )
    logger.info(f"Uploading {len(articles)} articles")

    session = create_session()

    uploaded_articles = []
    for article in articles:
        try:
            uploaded_article, success = upload_article(article, session)

            uploaded_articles.append(uploaded_article)
            logger.info(f"successfully uploaded article: {uploaded_article.title}")
        except Exception as e:
            logger.error(e)
            logger.error(f"failed to upload article: {article.title}")

    logger.info(
        f"successfully uploaded {len(uploaded_articles)}/{len(articles)} articles"
    )
