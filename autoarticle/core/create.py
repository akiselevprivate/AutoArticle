import click
from db.manage import create_db
from db.models import db_obj, Article, Action, ArticleLink
from settings.settings import settings
from utils.other import create_uuid_list, generate_seo_friendly_url
from utils.create import *
from utils.llm import global_input_token_usage, global_output_token_usage
import uuid as uuid_pkg


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

    action = Action.create(action_type="create", settings=settings_dump)

    if existing_titles or (not existing_titles and settings.EXISTING_TITLES):
        titles_list, title_uuid_list = get_existing_titles(settings.ARTICLE_TYPE)
        logger.info(f"using existing titles: {len(titles_list)}")
    else:
        titles_list, title_uuid_list = [], []

    logger.info(f"generating {settings.GEN_TITLES_COUNT} titles")

    new_titles, titles_token_usage = create_titles(
        titles_count if titles_count else settings.GEN_TITLES_COUNT
    )

    action.title_used_tokens = titles_token_usage
    action.save()

    # alternative_titles, alt_titles_token_usage = create_alternative_titles(new_titles)

    alternative_titles = new_titles  # TODO
    alt_titles_token_usage = 0

    action.alt_titles_used_tokens = alt_titles_token_usage
    action.save()

    articles = []

    for t, a in zip(new_titles, alternative_titles):
        url_ending = generate_seo_friendly_url(t)
        try:
            article = Article.create(
                action=action,
                article_type=settings.ARTICLE_TYPE,
                title=t,
                url_ending=url_ending,
                alternative_title=a,
            )
            articles.append(article)
        except:
            logger.info(f'artile with title: "{t}" already exists')

    logger.info(f"created {len(articles)}/{len(new_titles)} new articles")

    articles_count = articles_count if articles_count else settings.GEN_ARTICLES_COUNT

    valid_new_titles = [a.title for a in articles][:articles_count]
    valid_new_uuids = [str(a.id) for a in articles][:articles_count]
    # valid_alternative_titles = [a.alternative_title for a in article][:articles_count]

    titles_list += valid_new_titles
    title_uuid_list += valid_new_uuids

    outline_dict_list, outline_token_usage = create_outlines(
        valid_new_titles, titles_list, title_uuid_list
    )

    action.outline_used_tokens = outline_token_usage
    action.save()

    for article, outline in zip(articles, outline_dict_list):
        article.outline_json = json.dumps(outline)
        article.tags_json = json.dumps(outline["tags"])
        article.categories_json = json.dumps(outline["categories"])
        article.save()

        for _, linking_article_uuid in outline["outline"]:
            ArticleLink.create(from_article=article, to_article=linking_article_uuid)
            if str(article.id) == linking_article_uuid:
                logger.error(f"linking thesame article: {linking_article_uuid}")

    section_chunks, sections_used_tokens = create_section_chunks(
        valid_new_titles, titles_list, title_uuid_list, outline_dict_list
    )

    action.sections_used_tokens = sections_used_tokens
    action.save()

    success_count = 0

    for article, outline, section_chunk in zip(
        articles, outline_dict_list, section_chunks
    ):
        if outline:
            if all(section_chunk):
                success = True
                success_count += 1
            else:
                success = False
            article.sections_list_json = json.dumps(section_chunk)
        else:
            success = False

        article.is_complete = True
        article.is_succesful = success
        article.save()

        # converting uuids into urls in outline
        for idx, (_, linking_article_uuid) in enumerate(outline["outline"]):
            linking_article = Article.get_by_id(linking_article_uuid)
            outline["outline"][idx][1] = (
                settings.LINKING_URL_PATH + linking_article.url_ending
            )

        full_markdown = create_full_markdown(
            article.title, outline["outline"], section_chunk
        )
        article.full_article_markdown = full_markdown
        article.save()

    logger.info(f"Succesufully generated {success_count} articles")

    total_input_token_price = global_input_token_usage / 1000 * 0.0010
    total_output_token_price = global_output_token_usage / 1000 * 0.0020
    logger.info(
        f"Used {global_input_token_usage} input tokens, {global_output_token_usage} output tokens; which is {total_input_token_price+total_output_token_price:.4f}$"
    )
