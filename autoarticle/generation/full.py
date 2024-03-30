from generation.article import generate_outline, generate_section
from generation.embeddings import get_linking_articles, add_linking_embeddings
from generation.image import generate_hero_image
from generation.other import generate_categories, generate_titles
from generation.utils import generate_slug

from settings.settings import settings
from db.models import Article
from settings.logger import logger


def generate_articles(
    topic: str,
    categories_ammount: int,
    titles_ammount: int,
    sections_ammount: int,
    should_generate_hero_image: bool,
):
    categories = generate_categories(topic, categories_ammount)

    logger.info(f"Generated {categories_ammount} categories.")

    articles: list[Article] = []
    mult, rem = divmod(titles_ammount, categories_ammount)
    rem_count = 0
    for category in categories:
        local_ammount = mult
        if rem_count < rem:
            local_ammount += 1
            rem_count += 1
        # print(f"generating titles with {local_ammount} titles.")
        titles = generate_titles(topic, category, local_ammount)
        for title in titles:
            slug = generate_slug(title)
            article = Article.create(title=title, slug=slug, category=category)
            articles.append(article)

    logger.info(f"Generated {len(articles)} titles.")

    articles = continue_articles(articles, sections_ammount, should_generate_hero_image)

    return articles


def continue_articles(
    articles: list[Article], sections_ammount: int, should_generate_hero_image: bool
):

    for article in articles:
        if not article.section_titles:
            outline_dict = generate_outline(article.title, sections_ammount)
            sections = outline_dict["outline"]
            article.section_titles = sections
            article.save()

    logger.info(f"Generated outlines")

    titles = []
    section_titles = []
    uuids = []

    for article in articles:
        if not article.embedding_complete:
            titles.append(article.title)
            section_titles.append(article.section_titles)
            uuids.append(article.id)

    if titles:
        add_linking_embeddings(titles, section_titles, uuids)

    for article in articles:
        article.embedding_complete = True
        article.save()

    logger.info(f"Generated embeddings.")

    for article in articles:
        if not article.interlinking_uuids:
            linking_article_titles, linking_article_uuids = get_linking_articles(
                article.title, article.section_titles
            )
            article.interlinking_uuids = linking_article_uuids
            article.save()

    

    logger.info(f"Created linkings.")

    for idx, article in enumerate(articles):
        if not article.sections:
            logger.info(f"Generating article: {article.title}")
            section_titles = article.section_titles
            section_mds = []
            for section, linking_uuid in zip(
                section_titles, article.interlinking_uuids
            ):
                linking_title = Article.get_by_id(linking_uuid).title
                section_md = generate_section(
                    article.title, section, linking_title, section_titles
                )
                section_mds.append(section_md)
            article.sections = section_mds
            article.save()
        logger.info(f"Completed {idx+1}/{len(articles)} articles.")

    if should_generate_hero_image:
        for article in articles:
            if not article.image_description:
                image_description = generate_hero_image(article.title, article.id)
                article.image_description = image_description
                article.image_generated = True
                article.save()
        logger.info(f"Generated images.")

    for article in articles:
        article.is_complete = True
        article.save()

    logger.info(f"Finished generating {len(articles)} articles.")

    return articles
