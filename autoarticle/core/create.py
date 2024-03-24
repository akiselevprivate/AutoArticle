import click
from db.manage import create_db
from db.models import db_obj, Article
from settings.settings import settings
from generation.full import generate_articles, continue_articles

from utils.llm import rate_limiter
from settings.logger import logger
import json
import asyncio


@click.group()
def create():
    pass


def output_model_price():
    input_price, output_price = rate_limiter.calculate_total_price()
    logger.info(
        f"Used {input_price:.2f}$ for input tokens, {output_price:.2f}$ for output tokens, {output_price+input_price:.3f}$ total"
    )


@create.command()
def new():
    create_db(db_obj)

    articles = generate_articles(
        settings.TOPIC,
        settings.CATEGORIES_COUNT,
        settings.GEN_TITLES_COUNT,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.GENERATE_IMAGE,
    )

    output_model_price()


@create.command()
def existing():
    articles = Article.select().where(Article.is_complete == False)

    articles = continue_articles(
        articles,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.GENERATE_IMAGE,
    )

    output_model_price()
