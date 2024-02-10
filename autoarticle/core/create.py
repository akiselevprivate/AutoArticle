import click
from db.manage import create_db
from db.models import db_obj, Article, Action, ArticleLink
from settings.settings import settings
from utils.other import generate_seo_friendly_url
from utils.create import (
    continue_article,
    get_existing_titles_with_uuid,
    create_titles,
    process_articles_in_paralel,
    process_articles_sequentialy,
)
from utils.llm import rate_limiter
from settings.logger import logger
import json
import asyncio


@click.group()
def create():
    pass


@create.command()
@click.option("--titles-count", help="generate new titles ammount", type=int)
@click.option("--articles-count", help="generate new articles ammount", type=int)
@click.option(
    "--existing-titles/--no-existings-titles",
    help="use existing articles from db",
    type=bool,
)
def new(
    titles_count, articles_count, existing_titles
):  # dont use becuase settings dump into db wrong
    create_db(db_obj)

    settings_dump = settings.model_dump()
    if titles_count:
        settings_dump["GEN_TITLES_COUNT"] = titles_count
    if articles_count:
        settings_dump["GEN_ARTICLES_COUNT"] = articles_count
    if existing_titles:
        settings_dump["EXISTING_TITLES"] = existing_titles

    action = Action.create(action_type="create", settings=json.dumps(settings_dump))

    if existing_titles or (not existing_titles and settings.EXISTING_TITLES):
        linking_titles_with_uuids = get_existing_titles_with_uuid(settings.ARTICLE_TYPE)
        logger.info(f"using existing titles: {len(linking_titles_with_uuids)}")
    else:
        linking_titles_with_uuids = []

    logger.info(f"generating {settings.GEN_TITLES_COUNT} titles")

    titles_count = titles_count if titles_count else settings.GEN_TITLES_COUNT

    new_titles, titles_token_usage = create_titles(titles_count)

    # action.title_used_tokens = titles_token_usage
    # action.save()

    logger.info(f"generated {len(new_titles)}/{titles_count} new titles")

    articles = []

    for title in new_titles:
        url_ending = generate_seo_friendly_url(title)
        try:
            article = Article.create(
                action=action,
                article_type=settings.ARTICLE_TYPE,
                title=title,
                url_ending=url_ending,
            )
            articles.append(article)
        except Exception as e:
            logger.info(e)
            logger.info(f'article with title: "{title}" already exists')

    logger.info(f"created {len(articles)}/{len(new_titles)} new titles (acticles)")

    new_articles_count = (
        articles_count if articles_count else settings.GEN_ARTICLES_COUNT
    )

    gen_articles = articles[:new_articles_count]

    linking_titles_with_uuids += [[str(a.title), str(a.id)] for a in articles][
        :new_articles_count
    ]

    # finished_articles, success_list = process_articles_in_paralel(
    #     gen_articles, linking_titles_with_uuids
    # )

    finished_articles, success_list = process_articles_sequentialy(
        gen_articles, linking_titles_with_uuids
    )

    logger.info(
        f"Succesufully generated {sum(success_list)}/{new_articles_count} articles"
    )

    input_price, output_price = rate_limiter.calculate_total_price()
    logger.info(
        f"Used {input_price:.2f}$ for input tokens, {output_price:.2f}$ for output tokens, {output_price+input_price:.2f}$ total"
    )


# continue
@create.command()
@click.argument("actions", type=str)
@click.option("--articles-count", help="generate new articles ammount", type=int)
@click.option(
    "--existing-titles/--no-existings-titles",
    help="use existing articles from db",
    type=bool,
)
def existing(actions, articles_count, existing_titles):
    settings_dump = settings.model_dump()
    settings_dump["ACTIONS"] = actions
    action = Action.create(action_type="create", settings=json.dumps(settings_dump))
    if actions == "all":
        articles = (
            Article.select()
            .join(Action)
            .where(
                Article.article_type == settings.ARTICLE_TYPE,
                Article.is_complete == False,
            )
            .limit(articles_count)
        )
    else:
        articles = (
            Article.select()
            .join(Action)
            .where(
                Action.uuid == action,
                Article.article_type == settings.ARTICLE_TYPE,
                Article.is_complete == False,
            )
            .limit(articles_count)
        )

    if existing_titles or (not existing_titles and settings.EXISTING_TITLES):
        linking_titles_with_uuids = get_existing_titles_with_uuid(settings.ARTICLE_TYPE)
        logger.info(f"using existing titles: {len(linking_titles_with_uuids)}")
    else:
        linking_titles_with_uuids = []

    new_articles_count = (
        articles_count if articles_count else settings.GEN_ARTICLES_COUNT
    )

    linking_titles_with_uuids += [[str(a.title), str(a.id)] for a in articles][
        :new_articles_count
    ]

    finished_articles, success_list = process_articles_sequentialy(
        articles, linking_titles_with_uuids
    )

    logger.info(
        f"Succesufully finished {sum(success_list)}/{new_articles_count} articles"
    )

    input_price, output_price = rate_limiter.calculate_total_price()
    logger.info(
        f"Used {input_price:.2f}$ for input tokens, {output_price:.2f}$ for output tokens, {output_price+input_price:.2f}$ total"
    )
