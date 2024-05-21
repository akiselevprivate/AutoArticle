import click
from db.models import Article, Collection, Product
from settings.settings import settings
from generation.parts import (
    create_anchors,
    create_articles_base,
    create_linkings,
    generate_embeddings,
)
from generation.other import generate_title
from generation.utils import generate_slug

from utils.llm import rate_limiter
from settings.logger import logger
from settings.content import CONTENT_TYPES

import json
import pandas as pd
from itertools import cycle


@click.group()
def create():
    pass


def output_model_price():
    input_price, output_price = rate_limiter.calculate_total_price()
    logger.info(
        f"Used {input_price:.2f}$ for input tokens, {output_price:.2f}$ for output tokens, {output_price+input_price:.3f}$ total"
    )


def finish_generation(collections: list[Collection] = None):
    if not collections:
        collections: list[Collection] = Collection.select().order_by(
            Collection.id.asc()
        )

    articles = Article.select().where(Article.collection << collections)

    create_articles_base(
        articles,
        settings.ARTICLE_SECTIONS_COUNT,
        settings.EXTRA_IMAGES_PER_ARTICLE_PERCENTAGE,
        settings.ARTICLE_LINK_PERCENTAGE,
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
@click.argument("config", type=str)
@click.argument("distribution", type=str)
def config(config, distribution):
    article_csv_data = pd.read_csv(config).fillna("").values.tolist()

    distribution = eval(distribution)

    assert type(distribution) == list

    total_days = sum([i[0] for i in distribution])
    total_articles = sum([i[0] * i[1] for i in distribution])

    data = {}

    for d in article_csv_data:
        if d[1] not in data:
            data[d[1]] = []
        data[d[1]].append(d)

    out = []

    cats = cycle(data.keys())

    while len(out) != len(article_csv_data):
        cat = next(cats)
        if len(data[cat]) > 0:
            d = data[cat].pop()
            out.append(d)

    article_iterator = iter(out)

    print("total days: ", total_days)
    print("total articles: ", total_articles)

    print("total articles in csv: ", len(article_csv_data))

    assert total_articles <= len(article_csv_data)

    collections = []

    for days, amount in distribution:
        for _ in range(days):
            day = []
            for _ in range(amount):
                article_data = next(article_iterator)
                article_data = [str(d).strip() for d in article_data]
                article = {
                    "topic": article_data[0],
                    "category": article_data[1],
                    "tag": article_data[2],
                    "data_req": True,
                    "image_req": True,
                    "content_type": "BASIC",
                }
                day.append(article)
            collections.append(day)

    json.dump({"collections": collections}, open("config.json", "w+"), indent=2)
    print("Saved config to config.json")


@create.command()
@click.argument("config", type=click.File("r"))
@click.option("--only-titles", "-ot", is_flag=True)
def collections(config, only_titles):
    collections_config = json.load(config)

    collections = []
    articles: list[Article] = []

    for collection in collections_config["collections"]:
        collection_inst = Collection.create()
        collections.append(collection_inst)
        for a_data in collection:
            title, data_query = generate_title(
                a_data["topic"], a_data["category"], a_data["tag"]
            )
            try:
                article = Article.create(
                    collection=collection_inst,
                    article_type=CONTENT_TYPES[a_data["content_type"]]["type"],
                    tone=CONTENT_TYPES[a_data["content_type"]]["tone"],
                    expected_word_count=CONTENT_TYPES[a_data["content_type"]][
                        "word_count"
                    ],
                    title=title,
                    slug=generate_slug(title),
                    data_query=data_query,
                    topic=a_data["topic"],
                    category=a_data["category"],
                    tag=a_data["tag"],
                    data_req=a_data["data_req"],
                    image_req=a_data["image_req"],
                    content_type=a_data["content_type"],
                )
            except:
                logger.error("Duplicate title found")
            articles.append(article)

    logger.info(f"Created {len(articles)} articles")

    if only_titles:
        open("generated_titles.txt", "w+").write("\n".join([a.title for a in articles]))
        print("Saved titles to generated_titles.txt")
    else:
        finish_generation(collections)


@create.command()
def existing():
    finish_generation()
