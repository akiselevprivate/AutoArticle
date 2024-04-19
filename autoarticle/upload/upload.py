from settings.settings import settings
from db.models import Article, Section
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

import re
import requests
import json


def create_section_markdown(section: Section):
    markdown_components = []
    markdown_components.append(f"## {section.title}")

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
        section_markdown.replace(r"–", "-")
        .replace(r" - ", "    - ")
        .replace("## ", "### ")
        .replace("# ", "### ")
    )

    markdown_components.append(section_markdown)
    return "\n".join(markdown_components)


def upload_article(article: Article, session: requests.Session, categories_dict: dict):

    categorie_ids = [categories_dict[article.category]]

    post_data = {
        "title": article.title,
        "slug": article.slug,
        "excerpt": article.excerpt,
        "categories": categorie_ids,
        "status": settings.PUBLISH_STATUS,
    }

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

    full_html_list = []
    for section, image_tag in zip(sections, section_image_tags):
        section_markdown = create_section_markdown(section)
        section_html = markdown_to_html(section_markdown)
        if image_tag:
            full_html_list.append(image_tag)
        full_html_list.append(section_html)

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
