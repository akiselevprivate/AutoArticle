from settings.settings import settings
from db.models import Article, Section
from utils.other import (
    replace_urls_in_markdown,
    remove_first_h2_markdown,
    remove_title_from_markdown,
    markdown_to_html,
)
from settings.logger import logger

from generation.utils import get_sections, generate_slug

import json
import requests


def create_session():
    session = requests.Session()
    session.auth = (settings.WP_USER, settings.WP_APPLICATION_PASSWORD)
    return session


def upload_article_request(session: requests.Session, article_data: dict):
    url = settings.SITE_URL + "wp-json/wp/v2/posts"
    responce = session.post(url, json=article_data)
    return responce, responce.status_code == 201


def create_article_markdown(article: Article):
    markdown_components = []
    # if settings.UPLOAD_WITH_TITLE:
    #     markdown_components.append(f"# {article.title}")
    sections: list[Section] = get_sections(article.id)
    for section in sections:
        markdown_components.append(f"## {section.title}")

        linking_article_slug = section.link.slug
        suffix = settings.SUFFIX_URL + "/" if settings.SUFFIX_URL else ""
        linking_article_link = "/" + suffix + linking_article_slug + "/"

        section_markdown = remove_title_from_markdown(section.markdown)

        section_markdown = remove_first_h2_markdown(section_markdown)

        # if settings.REMOVE_TOP_H3:
        #     section_markdown = remove_first_h3_markdown(section_markdown)

        section_markdown = replace_urls_in_markdown(
            section_markdown, linking_article_link
        )

        section_markdown = section_markdown.replace(r"–", "-").replace(r" - ", "    - ")

        markdown_components.append(section_markdown)

    full_markdown = "\n".join(markdown_components)
    return full_markdown


def create_categorie_request(session: requests.Session, categorie_data: dict):
    url = settings.SITE_URL + "wp-json/wp/v2/categories"
    responce = session.post(url, json=categorie_data)
    # print(responce.text)
    json_responce = responce.json()
    categorie_id = None
    if responce.status_code == 201:
        categorie_id = json_responce["id"]
        success = True
    elif responce.status_code == 400 and responce.json()["code"] == "term_exists":
        categorie_id = json_responce["data"]["term_id"]
        success = True
    else:
        success = False

    return responce, success, categorie_id


def upload_media(session: requests.Session, file_path: str, alt_text: str):
    media = {"file": open(file_path, "rb"), "alt_text": alt_text, "title": alt_text}
    url = settings.SITE_URL + "wp-json/wp/v2/media"
    response = session.post(url, files=media)
    featured_image_id = response.json().get("id")
    assert featured_image_id != None
    return featured_image_id


def upload_article(article: Article, session: requests.Session, categories_dict: dict):
    content_markdown = create_article_markdown(article)
    content_html = markdown_to_html(content_markdown)

    categorie_ids = [categories_dict[article.category]]

    post_data = {
        "title": article.title,
        "slug": article.slug,
        "content": content_html,
        "categories": categorie_ids,
        "status": settings.PUBLISH_STATUS,
    }

    if article.image_generated:
        media_file_path = f"{settings.IMAGE_PATH}/{str(article.id)}.webp"
        featured_image_id = upload_media(
            session,
            media_file_path,
            article.image_description,
        )
        post_data["featured_media"] = featured_image_id

    responce, success = upload_article_request(session, post_data)

    if success:
        article.is_published = True
        article.save()
    else:
        logger.error("failed to upload article")
        logger.error(responce.json())

    return article, success
