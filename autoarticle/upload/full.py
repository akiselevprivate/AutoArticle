from db.models import Article
from settings.logger import logger
from settings.settings import settings
from upload.api import create_session, create_categorie_request, get_users
from upload.upload import upload_article

from generation.utils import generate_slug

import random


def upload_articles(articles: list[Article], date: str = None):
    logger.info(f"Uploading {len(articles)} articles to {settings.SITE_URL}")

    session = create_session()

    categories_db = articles.select(Article.category).distinct()

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

    users_dict = get_users(session)
    user_ids = []
    admin_id = None
    for d in users_dict:
        if d["name"] == "admin":
            admin_id = d["id"]
        else:
            user_ids.append(d["id"])

    if not user_ids:
        logger.info("Uploading as admin, no other accounts exist")

    uploaded_articles = []
    for idx, article in enumerate(articles):
        # try:

        if not user_ids:
            user_id = admin_id
        else:
            user_id = random.choice(user_ids)

        uploaded_article, success = upload_article(
            article, date, session, categorie_dict, user_id
        )

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
