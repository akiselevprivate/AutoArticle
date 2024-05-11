import click
import jsonschema.exceptions
from db.models import Article, Collection, Product
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
from settings.content import CONTENT_TYPES

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


def finish_generation(collections: list[Collection] = None):
    if not collections:
        collections: list[Collection] = Collection.select().order_by(
            Collection.id.asc()
        )

    articles = Article.select().where(Article.collection << collections)

    create_articles_base(
        articles,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.EXTRA_IMAGES_PER_ARTICLE,
        settings.ARTICLE_LINK_COUNT,
    )

    for col in collections:
        linking_articles: list[Article] = Article.select().where(
            Article.collection == col
        )
        generate_embeddings(linking_articles)
        create_linkings(linking_articles)

    create_anchors(articles)

    logger.info(f"Finished creating {len(articles)} article bases.")


@create.command()
@click.argument("config", type=click.File("r"))
@click.option("--only-titles", "-ot", is_flag=True)
def collections(config, only_titles):
    collections_config = json.load(config)

    gen_data = {}

    collections = []
    articles: list[Article] = []

    for collection in collections_config["collections"]:
        collection_inst = Collection.create()
        collections.append(collection_inst)
        for part in collection:
            if part["content_type"] not in CONTENT_TYPES.keys():
                raise Exception(f'"{part["article_type"]}" not a valid content type')

            if "articles" in part.keys():
                for art in part["articles"]:
                    try:
                        article = Article.create(
                            collection=collection_inst.id,
                            topic=part["topic"],
                            category=part["categories"][0],
                            article_type=CONTENT_TYPES[part["content_type"]]["type"],
                            tone=CONTENT_TYPES[part["content_type"]]["tone"],
                            title=art["title"],
                            slug=generate_slug(art["title"]),
                            additional_data=art["data"],
                            data_req=part["data_req"],
                            content_type=part["content_type"],
                            image_req=part["image_req"],
                        )

                        if "products" in art.keys():
                            for p in art["products"]:
                                product = Product.create(article=article, **p)

                        articles.append(article)
                    except Exception as e:
                        logger.error(f"Error creating article, probably duplicate: {e}")

            if part["amount"] == 0:
                continue

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
                cat_data = [
                    collection_inst.id,
                    amm,
                    part["data_req"],
                    part["image_req"],
                    part["content_type"],
                ]
                if cat not in gen_data[part["topic"]].keys():
                    gen_data[part["topic"]][cat] = [cat_data]
                else:
                    gen_data[part["topic"]][cat].append(cat_data)

    # json.dump(gen_data, open("dump.json", "w+"))
    # quit()

    def split_list(data, split):
        result = []
        start_index = 0

        for length in split:
            end_index = start_index + length
            result.append(data[start_index:end_index])
            start_index = end_index

        return result

    for topic, categories in gen_data.items():
        for cat, items in categories.items():
            amount = sum([i[1] for i in items])
            titles = generate_titles(topic, cat, amount)

            col_ids = [i[0] for i in items]
            split_amounts = [i[1] for i in items]
            split_data = split_list(titles, split_amounts)
            other_data = [i[2:] for i in items]

            for (
                titles,
                col_id,
                (data_req, image_req, content_type),
            ) in zip(split_data, col_ids, other_data):
                for title in titles:
                    try:
                        article = Article.create(
                            collection=col_id,
                            topic=topic,
                            category=cat,
                            article_type=CONTENT_TYPES[content_type]["type"],
                            tone=CONTENT_TYPES[content_type]["tone"],
                            title=title,
                            slug=generate_slug(title),
                            data_req=data_req,
                            image_req=image_req,
                            content_type=content_type,
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.error(f"Error creating article, probably duplicate: {e}")

    logger.info(f"Created {len(articles)} articles")

    if only_titles:
        open("titles.txt", "w+").write("\n".join([a.title for a in Article.select()]))
    else:
        finish_generation(collections)


@create.command()
def existing():
    finish_generation()
