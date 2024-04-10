import click
from db.models import Article
from settings.settings import settings
from generation.full import (
    generate_articles,
    continue_articles,
    gnerate_from_categories,
)

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

    articles = generate_articles(
        settings.TOPIC,
        settings.CATEGORIES_COUNT,
        settings.GEN_TITLES_COUNT,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.GENERATE_IMAGE,
        settings.ARTICLE_LINK_COUNT,
    )

    output_model_price()


@create.command()
@click.argument("categories", type=str)
def categories(categories):

    categories = categories.split(",")
    categories = [c.strip() for c in categories]

    gnerate_from_categories(
        settings.TOPIC,
        categories,
        settings.GEN_TITLES_COUNT,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.GENERATE_IMAGE,
        settings.ARTICLE_LINK_COUNT,
    )

    output_model_price()


@create.command()
@click.option("-c", "--count", "count", default=None)
def existing(count: int):
    articles = Article.select().where(Article.is_complete == False)

    if count:
        articles = articles.limit(int(count))

    articles = continue_articles(
        articles,
        settings.TOPIC,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.GENERATE_IMAGE,
        settings.ARTICLE_LINK_COUNT,
    )

    output_model_price()
