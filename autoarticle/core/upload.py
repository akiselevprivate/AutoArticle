import click
from settings.settings import settings
from db.models import Action, Article
from settings.logger import logger
from utils.upload import upload_articles
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
        articles = Article.select().where(
            Article.article_type == settings.ARTICLE_TYPE,
            Article.is_published == False,
            Article.is_complete,
            Article.is_succesful,
            # Action.is_deleted == False,
        )
    else:
        articles = Article.select().where(
            Action.uuid == action,
            Article.article_type == settings.ARTICLE_TYPE,
            Article.is_published == False,
            Article.is_complete,
            Article.is_succesful,
            # Action.is_deleted == False,
        )
    logger.info(f"Uploading {len(articles)} articles")

    successful_uploads = upload_articles(articles)

    logger.info(f"successfully uploaded {successful_uploads}/{len(articles)} articles")
