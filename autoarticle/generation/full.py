from generation.article import generate_outline, generate_section
from generation.embeddings import get_linking_articles, add_linking_embeddings
from generation.image import generate_hero_image
from generation.other import generate_categories, generate_titles, generate_anchors
from generation.utils import generate_slug, get_sections

from db.models import Article, Section
from settings.logger import logger
from utils.other import count_words_in_markdown

import time
import threading


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
        if not article.outline_generated:
            outline_dict = generate_outline(article.title, sections_ammount)
            sections = outline_dict["outline"]
            for idx, title in enumerate(sections):
                section = Section.get_or_create(article=article, title=title, idx=idx)
            article.outline_generated = True
            article.save()

    logger.info(f"Generated outlines")

    titles = []
    section_titles = []
    uuids = []

    for article in articles:
        if not article.embedding_complete:
            titles.append(article.title)
            section_titles.append([s.title for s in get_sections(article.id)])
            uuids.append(article.id)

    if titles:
        add_linking_embeddings(titles, section_titles, uuids)

    for article in articles:
        article.embedding_complete = True
        article.save()

    logger.info(f"Generated embeddings.")

    for article in articles:
        if not article.interlinking_uuids_generated:
            sections = get_sections(article.id)
            section_titles = [s.title for s in sections]
            linking_article_titles, linking_article_uuids = get_linking_articles(
                article.title, section_titles
            )
            for section, link in zip(sections, linking_article_uuids):
                section.link = link
                section.save()
            article.interlinking_uuids_generated = True
            article.save()

    logger.info(f"Created linkings.")

    anchor_generation_count = 0
    anchors_count = 0
    all_articles = Article.select()
    for article in all_articles:
        sections = Section.select().where(
            Section.anchor == None, Section.link == article
        )
        if sections.count() > 0:
            anchor_generation_count += 1
            anchors_count += sections.count()
            anchors = generate_anchors(article.title, ammount=sections.count())
            for section, anchor in zip(sections, anchors):
                section.anchor = anchor
                section.save()

    logger.info(
        f"Generated anchors: Invoked generation {anchor_generation_count} times, generated {anchors_count} anchors."
    )

    completion_times = []
    threads = []
    for idx, article in enumerate(articles):
        t1 = time.time()
        sections: list[Section] = Section.select().where(
            Section.markdown == None, Section.article == article
        )
        if sections.count() > 0:
            logger.info(
                f"Generating {sections.count()} sections for article: {article.title}"
            )
            all_section_titles = [s.title for s in get_sections(article.id)]
            for section in sections:

                def gen(section: Section):
                    section_md, generated_anchors = generate_section(
                        article.title,
                        section.title,
                        section.anchor,
                        section.link.title,
                        all_section_titles,
                    )
                    section.markdown = section_md
                    section.generated_anchors = generated_anchors
                    section.generated_links_count = len(generated_anchors)
                    section.word_count = count_words_in_markdown(section_md)

                    section.save()

                thread = threading.Thread(target=gen, args=(section,))
                thread.start()
                threads.append(thread)

            [t.join() for t in threads]

            completion_t = time.time() - t1
            completion_times.append(completion_t)
            logger.info(
                f"Completed {idx+1}/{len(articles)} articles. eta: {sum(completion_times)/len(completion_times)*(len(articles) - idx + 1)/60:.0f} mins"
            )

    logger.info("Generated sections.")

    if should_generate_hero_image:
        for article in articles:
            if not article.image_generated:
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
