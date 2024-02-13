import click
from settings.settings import settings
from db.models import Action, Article, Categorie
from settings.logger import logger
from utils.upload import upload_article, create_session, create_categorie_request
from utils.other import generate_seo_friendly_url
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

    categorie_dict = {}
    categories = Categorie.select()

    for cat in categories:
        term = cat.term
        cat_data = dict(
            slug=generate_seo_friendly_url(term),
            name=term,
        )
        responce, success, categorie_id = create_categorie_request(session, cat_data)
        if not success:
            logger.error(responce.json())
            raise Exception("failed creating categorie")
        categorie_dict[term] = categorie_id

    logger.info(f"Uploaded {len(categories)} categories")

    uploaded_articles = []
    for article in articles:
        try:
            uploaded_article, success = upload_article(article, session, categorie_dict)

            uploaded_articles.append(uploaded_article)
            logger.info(f"successfully uploaded article: {uploaded_article.title}")
        except Exception as e:
            logger.error(e)
            logger.error(f"failed to upload article: {article.title}")

    logger.info(
        f"successfully uploaded {len(uploaded_articles)}/{len(articles)} articles"
    )
