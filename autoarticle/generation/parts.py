from generation.article import generate_outline, generate_section
from generation.embeddings import get_linking_articles, add_linking_embeddings
from generation.image import (
    generate_hero_image_from_prompt,
    generate_hero_prompt,
    generate_section_prompt,
)
from generation.other import (
    generate_anchors,
    generate_addiional_data,
    generate_split_data,
)
from generation.utils import get_sections, generate_random_bool_list
from generation.product import generate_product_outline
from generation.faq import generate_faq

from db.models import Article, Section, Product
from settings.logger import logger
from utils.other import count_words_in_markdown, batch
from utils.youtube import get_video_url

import time
import threading
import math


# def create_article_titles(
#     topic: str,
#     categories: list[str],
#     titles_ammount: int,
# ):

#     articles: list[Article] = []
#     mult, rem = divmod(titles_ammount, len(categories))
#     rem_count = 0
#     for category in categories:
#         local_ammount = mult
#         if rem_count < rem:
#             local_ammount += 1
#             rem_count += 1
#         titles = generate_titles(topic, category, local_ammount)
#         for title in titles:
#             slug = generate_slug(title)
#             try:
#                 article = Article.create(
#                     title=title, slug=slug, category=category, topic=topic
#                 )
#                 articles.append(article)
#             except Exception as e:
#                 logger.error(e)
#                 logger.error("Error creating article")

#     logger.info(f"Generated {len(articles)} titles.")

#     return articles


# def generate_from_categories(
#     topic: str,
#     categories: list[str],
#     titles_ammount: int,
#     sections_ammount: int,
#     should_generate_hero_image: bool,
#     links_per_article: int,
#     images_per_article: int,
# ):
#     articles = create_articles_from_title(topic, categories, titles_ammount)

#     articles = continue_articles(
#         articles,
#         sections_ammount,
#         should_generate_hero_image,
#         links_per_article,
#         images_per_article,
#     )

#     return articles


# def generate_articles(
#     topic: str,
#     categories_ammount: int,
#     titles_ammount: int,
#     sections_ammount: int,
#     should_generate_hero_image: bool,
#     links_per_article: int,
#     images_per_article: int,
# ):
#     categories = generate_categories(topic, categories_ammount)

#     logger.info(f"Generated {categories_ammount} categories.")

#     articles = generate_from_categories(
#         topic,
#         categories,
#         titles_ammount,
#         sections_ammount,
#         should_generate_hero_image,
#         links_per_article,
#         images_per_article,
#     )

#     return articles


def create_articles_base(
    articles: list[Article],
    min_sections_count: int,
    max_sections_count: int,
    images_per_article_percentage: int,
    links_per_article_percentage: int,
):
    for article in articles:
        if article.data_req and not article.additional_data:
            additional_data = generate_addiional_data(article.data_query)
            article.additional_data = additional_data
            article.save()

    logger.info("Generated additional data")

    for article in articles:
        products: list[Product] = Product.select().where(
            Product.article == article, Product.is_generated == False
        )
        for product in products:
            product_outline = generate_product_outline(
                product.description,
                product.reviews,
                product.full_name,
                product.price,
            )
            product.pros = product_outline["pros"]
            product.cons = product_outline["cons"]
            product.short_name = product_outline["short_name"]
            product.summary = product_outline["summary"]
            product.is_generated = True
            product.save()

    logger.info(f"Generated product outlines.")

    for article in articles:
        if not article.outline_generated:

            products: list[Product] = Product.select().where(Product.article == article)

            # if article.content_type == "PRODUCT_REVIEW":
            #     additional_data = products[0].summary
            # else:
            #     additional_data = article.additional_data

            # if article.content_type == "PRODUCT_COMPARISON":
            #     sections_ammount = products.count() + 2
            # else:
            #     products = [None] * default_sections_ammount
            #     sections_ammount = default_sections_ammount

            assert article.content_type == "BASIC"

            outline_dict = generate_outline(
                article.title,
                min_sections_count, 
                max_sections_count,
                article.topic,
                article.category,
                additional_data,
                article.article_type,
                article.tone,
                article.content_type,
            )
            sections = outline_dict["outline"]
            sections_ammount = len(outline_dict["outline"])

            products = [None] * sections_ammount

            # if article.content_type == "PRODUCT_COMPARISON":
            #     sections = (
            #         [sections[0]] + [p.short_name for p in products] + [sections[-1]]
            #     )
            #     products = [None] + list(products) + [None]

            available_linking_articles_count = (
                Article.select().where(Article.collection <= article.collection).count()
                - 1
            )
            linking_articles_amount = math.ceil(
                sections_ammount * links_per_article_percentage
            )

            if linking_articles_amount > available_linking_articles_count:
                linking_articles_amount = available_linking_articles_count

            sections_inlude_link = generate_random_bool_list(
                sections_ammount, linking_articles_amount
            )

            if article.content_type == "PRODUCT_COMPARISON":
                sections_include_image = [False] * sections_ammount
            else:
                sections_include_image = [False] + generate_random_bool_list(
                    sections_ammount - 1,
                    math.ceil(sections_ammount * images_per_article_percentage),
                )
            section_word_count = int(article.expected_word_count / len(sections))
            for idx, (title, include_link, include_image, product) in enumerate(
                zip(sections, sections_inlude_link, sections_include_image, products)
            ):
                section = Section.create(
                    article=article,
                    title=title,
                    idx=idx,
                    include_link=include_link,
                    include_image=include_image,
                    product=product,
                    expected_word_count=section_word_count,
                )
            article.excerpt = outline_dict["excerpt"]
            article.video_query = outline_dict["video_query"]
            article.outline_generated = True
            article.save()

    logger.info(f"Generated outlines")


def generate_embeddings(articles: list[Article]):
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


def create_linkings(articles: list[Article]):
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


def create_anchors(articles: list[Article]):
    anchor_generation_count = 0
    anchors_count = 0
    all_articles: list[Article] = Article.select()
    for article in all_articles:
        sections = Section.select().where(
            Section.anchor == None,
            Section.link == article,
            Section.include_link == True,
            Section.article << articles,
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


def generate_articles(
    articles: list[Article],
    faq_amount: int,
    should_generate_hero_image: bool,
):

    create_anchors(articles)

    for article in articles:
        if article.data_req and not article.additional_data_split:
            sections: list[Section] = get_sections(article.id)

            section_titles = [s.title for s in sections]
            data_paragraphs = generate_split_data(
                article.title, article.additional_data, sections.count(), section_titles
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

                    if section.additional_data:
                        additional_data = section.additional_data
                    elif section.product:
                        additional_data = section.product.summary
                    else:
                        additional_data = None

                    section_md, generated_anchors = generate_section(
                        article.title,
                        section.title,
                        all_section_titles,
                        additional_data,
                        article.article_type,
                        article.tone,
                        section.include_link,
                        section.expected_word_count,
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

    for article in articles:
        if not article.faq:
            faq_2d = generate_faq(
                article.additional_data, article.topic, article.title, faq_amount
            )
            article.faq = faq_2d
            article.save()

    logger.info(f"Generated FAQs")

    if should_generate_hero_image:

        for article in articles:
            if not article.image_req:
                continue

            if not article.image_description:
                image_description = generate_hero_prompt(article.title)
                article.image_description = image_description
                article.save()

            sections: list[Section] = Section.select().where(
                Section.article == article,
                Section.include_image == True,
                Section.image_id == None,
            )

            for section in sections:
                if not section.image_description:
                    image_description = generate_section_prompt(
                        article.title, section.title
                    )
                    section.image_description = image_description
                    section.save()

        def gen_main_img(article: Article, array: list):
            image_description = article.image_description
            image_uuid = generate_hero_image_from_prompt(image_description)
            article.image_id = image_uuid
            array.append(article)

        def gen_section_img(section: Section, array: list):
            image_description = section.image_description
            image_uuid = generate_hero_image_from_prompt(image_description)
            section.image_id = image_uuid
            array.append(section)

        db_obj_list = []
        article_batches = batch(articles, 2)  # 3x5 (3x amount of images per article)
        for article_batch in article_batches:
            threads = []

            for article in article_batch:

                if article.image_req and not article.image_id:
                    gen_main_img(article, db_obj_list)
                    thread = threading.Thread(
                        target=gen_main_img, args=(article, db_obj_list)
                    )
                    thread.start()
                    threads.append(thread)

                if article.image_req:
                    sections: list[Section] = Section.select().where(
                        Section.article == article,
                        Section.include_image == True,
                        Section.image_id == None,
                    )
                    for section in sections:
                        thread = threading.Thread(
                            target=gen_section_img, args=(section, db_obj_list)
                        )
                        thread.start()
                        threads.append(thread)

            [t.join() for t in threads]  # wait for batch to complete

            for obj in db_obj_list:
                obj.save()

        logger.info(f"Generated images.")

    for article in articles:
        if not article.youtube_embed_url:
            article.youtube_embed_url = get_video_url(article.video_query)
            article.save()

    logger.info("Got youtube urls")

    for article in articles:
        article.is_complete = True
        article.save()

    logger.info(f"Finished generating {len(articles)} articles.")

    return articles
