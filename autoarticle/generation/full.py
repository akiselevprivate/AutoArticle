from generation.article import generate_outline, generate_section
from generation.embeddings import get_linking_articles, add_linking_embeddings
from generation.image import (
    generate_hero_image_from_prompt,
    generate_hero_prompt,
    generate_section_prompt,
)
from generation.other import (
    generate_categories,
    generate_titles,
    generate_anchors,
    generate_addiional_data,
    generate_split_data,
)
from generation.utils import generate_slug, get_sections, generate_random_bool_list

from db.models import Article, Section
from settings.logger import logger
from utils.other import count_words_in_markdown
from utils.youtube import get_video_url

import time
import threading


def create_articles_from_title(
    topic: str,
    categories: list[str],
    titles_ammount: int,
):

    articles: list[Article] = []
    mult, rem = divmod(titles_ammount, len(categories))
    rem_count = 0
    for category in categories:
        local_ammount = mult
        if rem_count < rem:
            local_ammount += 1
            rem_count += 1
        titles = generate_titles(topic, category, local_ammount)
        for title in titles:
            slug = generate_slug(title)
            try:
                article = Article.create(title=title, slug=slug, category=category)
                articles.append(article)
            except Exception as e:
                logger.error(e)
                logger.error("Error creating article")

    logger.info(f"Generated {len(articles)} titles.")

    return articles


def gnerate_from_categories(
    topic: str,
    categories: list[str],
    titles_ammount: int,
    sections_ammount: int,
    should_generate_hero_image: bool,
    links_per_article: int,
    images_per_article: int,
):
    articles = create_articles_from_title(topic, categories, titles_ammount)

    articles = continue_articles(
        articles,
        topic,
        sections_ammount,
        should_generate_hero_image,
        links_per_article,
        images_per_article,
    )

    return articles


def generate_articles(
    topic: str,
    categories_ammount: int,
    titles_ammount: int,
    sections_ammount: int,
    should_generate_hero_image: bool,
    links_per_article: int,
    images_per_article: int,
):
    categories = generate_categories(topic, categories_ammount)

    logger.info(f"Generated {categories_ammount} categories.")

    articles = gnerate_from_categories(
        topic,
        categories,
        titles_ammount,
        sections_ammount,
        should_generate_hero_image,
        links_per_article,
        images_per_article,
    )

    return articles


def continue_articles(
    articles: list[Article],
    topic: str,
    sections_ammount: int,
    should_generate_hero_image: bool,
    links_per_article: int,
    images_per_article: int,
):

    for article in articles:
        if not article.additional_data:
            additional_data = generate_addiional_data(article.title)
            article.additional_data = additional_data
            article.save()

    logger.info("Generated additional data")

    for article in articles:
        if not article.outline_generated:
            outline_dict = generate_outline(
                article.title,
                sections_ammount,
                topic,
                article.category,
                article.additional_data,
            )
            sections = outline_dict["outline"]
            sections_inlude_link = generate_random_bool_list(
                sections_ammount, links_per_article
            )
            sections_include_image = [0] + generate_random_bool_list(
                sections_ammount - 1, images_per_article
            )
            for idx, (title, include_link, include_image) in enumerate(
                zip(sections, sections_inlude_link, sections_include_image)
            ):
                section = Section.create(
                    article=article,
                    title=title,
                    idx=idx,
                    include_link=include_link,
                    include_image=include_image,
                )
            article.excerpt = outline_dict["excerpt"]
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
            sections = (
                Section.select()
                .where(Section.article == article.id, Section.include_link == True)
                .order_by(Section.idx.asc())
            )
            section_titles = [s.title for s in sections]
            linking_article_uuids = get_linking_articles(article.title, section_titles)
            for section, link in zip(sections, linking_article_uuids):
                section.link = link
                section.save()
            article.interlinking_uuids_generated = True
            article.save()

    logger.info(f"Created linkings.")

    anchor_generation_count = 0
    anchors_count = 0
    all_articles: list[Article] = Article.select()
    for article in all_articles:
        sections = Section.select().where(
            Section.anchor == None,
            Section.link == article,
            Section.include_link == True,
        )
        if sections.count() > 0:

            req_anchors_ammount = sections.count()

            genrate_anchors_ammount = req_anchors_ammount - len(
                article.additional_anchors
            )

            additional_anchors_left = (
                len(article.additional_anchors) - req_anchors_ammount
            )

            if additional_anchors_left < 0:
                additional_anchors_left = 0

            if genrate_anchors_ammount > 0:
                existing_anchors = [
                    s.anchor
                    for s in Section.select().where(
                        Section.link == article, Section.anchor != None
                    )
                ]

                # additional_anchors_ammount = (
                #     0
                #     if len(article.additional_anchors)
                #     > int(genrate_anchors_ammount * 0.1)
                #     else int(genrate_anchors_ammount * 0.1)
                # )

                anchors = generate_anchors(
                    article.title,
                    genrate_anchors_ammount,
                    existing_anchors,
                )
                anchor_generation_count += 1
                anchors_count += genrate_anchors_ammount

                use_anchors = (
                    anchors[:genrate_anchors_ammount]
                    + article.additional_anchors[additional_anchors_left:]
                )
                save_anchors = anchors[genrate_anchors_ammount:]

            else:
                use_anchors = article.additional_anchors[additional_anchors_left:]
                save_anchors = article.additional_anchors[:additional_anchors_left]

            article.additional_anchors = save_anchors
            article.save()

            for section, anchor in zip(sections, use_anchors):
                section.anchor = anchor
                section.save()

    logger.info(
        f"Generated anchors: Invoked generation {anchor_generation_count} times, generated {anchors_count} anchors."
    )

    for article in articles:
        if not article.additional_data_split:
            sections: list[Section] = get_sections(article.id)

            data_paragraphs = generate_split_data(
                article.title, article.additional_data, sections_ammount
            )

            for section, data in zip(sections, data_paragraphs):
                section.additional_data = data
                section.save()

            article.additional_data_split = True

    logger.info("Generated data split.")

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
                        all_section_titles,
                        section.additional_data,
                        section.include_link,
                        section.anchor if section.include_link else None,
                        section.link.title if section.include_link else None,
                    )
                    section.markdown = section_md

                    if section.include_link:
                        section.generated_anchor = generated_anchors[0]

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

    db_lock = threading.Lock()

    if should_generate_hero_image:
        threads = []
        for article in articles:

            def gen_img(article: Article):
                sections: list[Section] = Section.select().where(
                    Section.article == article,
                    Section.include_image == True,
                    Section.image_id == None,
                )
                if not article.image_id:
                    if not article.image_description:
                        image_description = generate_hero_prompt(article.title)
                        article.image_description = image_description
                        article.save()
                    else:
                        image_description = article.image_description
                    image_uuid = generate_hero_image_from_prompt(image_description)
                    article.image_id = image_uuid
                    article.save()
                for section in sections:
                    if not section.image_description:
                        image_description = generate_section_prompt(
                            article.title, section.title
                        )
                        section.image_description = image_description
                        section.save()
                    else:
                        image_description = section.image_description
                    image_uuid = generate_hero_image_from_prompt(image_description)
                    section.image_id = image_uuid
                    section.save()

            # thread = threading.Thread(target=gen_img, args=(article,))
            # thread.start()
            # threads.append(thread)
            gen_img(article)

        # [t.join() for t in threads]

        logger.info(f"Generated images.")

    for article in articles:
        if not article.youtube_embed_url:
            article.youtube_embed_url = get_video_url(article.title)
            article.save()

    logger.info("Got youtube urls")

    for article in articles:
        article.is_complete = True
        article.save()

    logger.info(f"Finished generating {len(articles)} articles.")

    return articles
