from settings.settings import settings
from db.models import Article
from utils.other import (
    replace_urls_in_markdown,
    remove_first_h2_markdown,
    remove_title_from_markdown,
    markdown_to_html,
)
from settings.logger import logger

import requests


def create_session():
    session = requests.Session()
    session.auth = (settings.WP_USER, settings.WP_APPLICATION_PASSWORD)
    return session


def upload_article_request(session: requests.Session, article_data: dict):
    url = settings.SITE_URL + "wp-json/wp/v2/posts"
    responce = session.post(url, json=article_data)
    return responce, responce.status_code == 201


def upload_articles(articles: list[Article]):
    session = create_session()
    successful_uploads = 0
    for article in articles:
        markdown_str = str(article.full_article_markdown)
        if not settings.UPLOAD_WITH_TITLE:
            markdown_str = remove_title_from_markdown(markdown_str)
            # logger.debug("markdown without title")
            # logger.debug(markdown_str)
        html = markdown_to_html(markdown_str)
        data = {
            "title": article.title,
            "slug": article.url_ending,
            "content": html,
            # "categories": "categorie,cat2",
            # "tags": "tag",
            "status": "private",
        }
        responce, success = upload_article_request(session, data)

        if success:
            successful_uploads += 1
            article.is_published = True
            article.save()
        else:
            logger.error(f"Failed to upload {article.title}")
            logger.error(responce.json())

    return successful_uploads


def create_full_markdown(
    title: str, sections_list: dict, section_chunk: list, include_title: bool
):
    content_list = []
    if include_title:
        content_list.append(
            f"# {title}",
        )

    for (section_title, replace_url), section_md in zip(sections_list, section_chunk):
        content_list.append(f"## {section_title}")
        if settings.REMOVE_TOP_H2:
            section_md = remove_first_h2_markdown(section_md)
        url_replaced_md = replace_urls_in_markdown(section_md, replace_url)
        content_list.append(url_replaced_md)

    markdown_string = "\n".join(content_list)
    return markdown_string
