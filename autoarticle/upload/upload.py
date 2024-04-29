from settings.settings import settings
from db.models import Article, Section, Product
from utils.other import (
    replace_urls_in_markdown,
    remove_first_h2_markdown,
    remove_title_from_markdown,
    remove_duplicate_h3,
    remove_first_h3,
    markdown_to_html,
)
from utils.youtube import video_embed_html, extract_video_id
from settings.logger import logger

from generation.utils import get_sections
from upload.utils import trim_newlines
from upload.api import upload_media, upload_article_request
from upload.blocks import (
    create_product_group,
    create_product_item,
    product_review_2_block,
)

import re
import requests
import json

# from itertools import zip_longest


def create_section_markdown(section: Section):
    markdown_components = []

    if section.product:
        markdown_components.append("### Product table (demo only)")
        markdown_components.append(f"Price: ${section.product.price}")
        markdown_components.append("#### Pros")
        for item in section.product.pros:
            markdown_components.append(f"- {item}")
        markdown_components.append("#### Cons")
        for item in section.product.cons:
            markdown_components.append(f"- {item}")
        markdown_components.append(f"[{section.product.short_name} on Amazon    ]()")
        markdown_components.append("---")

    section_markdown = section.markdown

    if section.include_link:
        linking_article_slug = section.link.slug
        suffix = settings.SUFFIX_URL + "/" if settings.SUFFIX_URL else ""
        linking_article_link = "/" + suffix + linking_article_slug + "/"

        section_markdown = replace_urls_in_markdown(
            section_markdown, linking_article_link
        )

    section_markdown = trim_newlines(section_markdown)

    section_markdown = remove_title_from_markdown(section_markdown)

    section_markdown = remove_first_h2_markdown(section_markdown)

    section_markdown = remove_duplicate_h3(section_markdown, section.title)

    if settings.REMOVE_FIRST_H3 and section.index == 0:
        section_markdown = remove_first_h3(section_markdown)

    section_markdown = (
        section_markdown.replace(r"–", "-").replace(r" - ", "    - ")
        # .replace("## ", "### ")
        # .replace("# ", "### ")
    )

    markdown_components.append(section_markdown)
    return "\n".join(markdown_components)


def upload_article(
    article: Article, date: str, session: requests.Session, categories_dict: dict
):

    categorie_ids = [categories_dict[article.category]]

    post_data = {
        "title": article.title,
        "slug": article.slug,
        "excerpt": article.excerpt,
        "categories": categorie_ids,
        "status": settings.PUBLISH_STATUS,
    }

    if date:
        post_data["date"] = date

    if article.image_id:  # TODO
        media_file_path = f"{settings.IMAGE_PATH}/{article.image_id}.webp"
        featured_image_id, _ = upload_media(
            session,
            media_file_path,
            article.image_description,
        )
        post_data["featured_media"] = featured_image_id

    sections: list[Section] = get_sections(article.id)
    section_image_tags = []
    section_product_tags = []
    product_group_items = []
    for section in sections:
        if section.image_id:
            media_file_path = f"{settings.IMAGE_PATH}/{section.image_id}.webp"
            _, image_tag = upload_media(
                session,
                media_file_path,
                section.image_description,
            )
            section_image_tags.append(image_tag)
        else:
            section_image_tags.append(None)
        if section.product:
            product_item_tag = create_product_item(
                section.product.short_name,
                section.product.rating,
                section.product.pros[0],
                section.product.image_url,
                f"{section.product.short_name} product image.",
                f"${section.product.price} on {section.product.source_names[0]}",
                section.product.urls[0],
            )
            product_group_items.append(product_item_tag)
            product_review_tag = product_review_2_block(
                section.product.short_name,
                section.product.rating,
                section.product.pros,
                section.product.cons,
                section.product.image_url,
                f"{section.product.short_name} product image.",
                [f"${section.product.price} on {section.product.source_name}"],
                [section.product.url],
            )
            section_product_tags.append(product_review_tag)
        else:
            section_product_tags.append(None)

    full_html_list = []
    for idx, (section, image_tag, product_review_tag) in enumerate(zip(
        sections, section_image_tags, section_product_tags
    )):
        section_markdown = create_section_markdown(section)
        section_html = markdown_to_html(section_markdown)
        if image_tag:
            full_html_list.append(image_tag)

        if product_review_tag:
            full_html_list.append(product_review_tag)
        else:
            full_html_list.append(f"## {section.title}")
        full_html_list.append(section_html)

        if idx == 0 and product_group_items:
            product_list_html = create_product_group(product_group_items)
            full_html_list.append(product_list_html)


    if article.faq:
        full_html_list.append(markdown_to_html("### FAQ"))
        for question, answer in article.faq:
            full_html_list.append(markdown_to_html(f"#### {question.capitalize()}"))
            full_html_list.append(markdown_to_html(answer.capitalize()))

    if article.youtube_embed_url:
        video_id = extract_video_id(article.youtube_embed_url)
        youtube_header = markdown_to_html(f"## Usefull video on {article.title}")
        full_html_list.append(youtube_header)
        full_html_list.append(video_embed_html(video_id))

    full_html = "\n".join(full_html_list)

    post_data["content"] = full_html

    responce, success = upload_article_request(session, post_data)

    if success:
        article.is_published = True
        article.save()
    else:
        logger.error("failed to upload article")
        logger.error(responce.json())

    return article, success
