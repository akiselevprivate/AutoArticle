import click
import jsonschema.exceptions
from db.models import Article, Collection
from settings.settings import settings
from generation.parts import (
    create_anchors,
    create_articles_base,
    create_linkings,
    generate_embeddings,
)
from generation.other import generate_categories, generate_titles
from generation.utils import generate_slug

from utils.llm import rate_limiter
from settings.logger import logger
from settings.schemas import collection_schema

import json
import jsonschema


@click.group()
def create():
    pass


def output_model_price():
    input_price, output_price = rate_limiter.calculate_total_price()
    logger.info(
        f"Used {input_price:.2f}$ for input tokens, {output_price:.2f}$ for output tokens, {output_price+input_price:.3f}$ total"
    )


# @create.command()
# def new():

#     articles = generate_articles(
#         settings.TOPIC,
#         settings.CATEGORIES_COUNT,
#         settings.GEN_TITLES_COUNT,
#         settings.ARTICLE_SECTIONS_COUNT,
#         settings.GENERATE_IMAGE,
#         settings.ARTICLE_LINK_COUNT,
#         settings.EXTRA_IMAGES_PER_ARTICLE,
#     )

#     output_model_price()


# @create.command()
# @click.argument("categories", type=str)
# def categories(categories):

#     categories = categories.split(",")
#     categories = [c.strip() for c in categories]

#     gnerate_from_categories(
#         settings.TOPIC,
#         categories,
#         settings.GEN_TITLES_COUNT,
#         settings.ARTICLE_SECTIONS_COUNT,
#         settings.GENERATE_IMAGE,
#         settings.ARTICLE_LINK_COUNT,
#         settings.EXTRA_IMAGES_PER_ARTICLE,
#     )

#     output_model_price()


# @create.command()
# @click.option("-c", "--count", "count", default=None)
# def existing(count: int):
#     articles = Article.select().where(Article.is_complete == False)

#     if count:
#         articles = articles.limit(int(count))

#     articles = continue_articles(
#         articles,
#         settings.TOPIC,
#         settings.ARTICLE_SECTIONS_COUNT,
#         settings.GENERATE_IMAGE,
#         settings.ARTICLE_LINK_COUNT,
#         settings.EXTRA_IMAGES_PER_ARTICLE,
#     )

#     output_model_price()


@create.command()
@click.argument("config", type=click.File("r"))
def collections(config):
    collections_config = json.load(config)

    # print(collections_config)
    # try:
    #     jsonschema.validate(collection_schema, collection_schema)
    # except jsonschema.exceptions.ValidationError as e:
    #     print("Invalid collections config schema:", e)
    #     return

    gen_data = {}

    import uuid as uuid_pkg

    collection_ids = []

    for collection in collections_config["collections"]:
        collection_id = Collection.create().id
        collection_ids.append(collection_id)
        for part in collection:
            if type(part["categories"]) == int:
                categories = generate_categories(part["topic"], part["categories"])
            else:
                categories = part["categories"]

            ammount_per_category, remainder_ammount = divmod(
                part["amount"], len(categories)
            )
            if part["topic"] not in gen_data.keys():
                gen_data[part["topic"]] = {}
            ammount_list = [ammount_per_category + remainder_ammount] + [
                ammount_per_category
            ] * (len(categories) - 1)
            for cat, amm in zip(categories, ammount_list):
                cat_data = [collection_id, amm]
                if cat not in gen_data[part["topic"]].keys():
                    gen_data[part["topic"]][cat] = [cat_data]
                else:
                    gen_data[part["topic"]][cat].append(cat_data)

    def split_list(data, split):
        result = []
        start_index = 0

        for length in split:
            end_index = start_index + length
            result.append(data[start_index:end_index])
            start_index = end_index

        return result

    articles: list[Article] = []

    for topic, categories in gen_data.items():
        for cat, items in categories.items():
            amount = sum([i[1] for i in items])
            titles = generate_titles(topic, cat, amount)

            col_ids = [i[0] for i in items]
            split_amounts = [i[1] for i in items]
            split_data = split_list(titles, split_amounts)

            for titles, col_id in zip(split_data, col_ids):
                for title in titles:
                    try:
                        article = Article.create(
                            collection=col_id,
                            topic=topic,
                            category=cat,
                            title=title,
                            slug=generate_slug(title),
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.error(f"Error creating article, probably duplicate: {e}")

    logger.info("Created articles")

    create_articles_base(
        articles,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.EXTRA_IMAGES_PER_ARTICLE,
        settings.ARTICLE_LINK_COUNT,
    )

    generate_embeddings(articles)

    for col_id in collection_ids:
        linking_articles: list[Article] = Article.select().where(
            Article.collection == col_id
        )
        create_linkings(linking_articles)

    create_anchors(articles)

    logger.info(f"Finished creating {len(articles)} articles")
