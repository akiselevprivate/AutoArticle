from settings.settings import settings
from db.models import Article
from utils.other import (
    replace_urls_in_markdown,
    remove_first_h2_markdown,
    remove_title_from_markdown,
    markdown_to_html,
    generate_seo_friendly_url,
)
from settings.logger import logger

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
    if settings.UPLOAD_WITH_TITLE:
        markdown_components.append(f"# {article.title}")
    outline_dict = json.loads(article.outline_json)
    article_sections = json.loads(article.sections_list_json)
    linking_uuids = json.loads(article.interlinking_uuids_json)
    for section, section_markdown, linking_uuid in zip(
        outline_dict["outline"], article_sections, linking_uuids
    ):
        markdown_components.append(f"## {section['title']}")

        linking_article_slug = Article.get_by_id(linking_uuid).url_ending
        linking_article_link = settings.SITE_URL + linking_article_slug

        if settings.REMOVE_TOP_H2:
            section_markdown = remove_first_h2_markdown(section_markdown)

        section_markdown = replace_urls_in_markdown(
            section_markdown, linking_article_link
        )

        markdown_components.append(section_markdown)

    # if settings.UPLOAD_WITH_FAQ:
    #     faq_markdown = create_faq_block(json.loads(article.faq_json))
    #     markdown_components.append(faq_markdown)

    full_markdown = "\n".join(markdown_components)
    return full_markdown


def create_categorie_request(session: requests.Session, categorie_data: dict):
    url = settings.SITE_URL + "wp-json/wp/v2/categories"
    responce = session.post(url, json=categorie_data)
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


def create_faq_block(faq_content: list):
    content = ["## FAQ"]
    for question, answer in faq_content:
        content.append(f"### {question}")
        content.append(answer)
    return "\n".join(content)


def upload_media(session: requests.Session, file_path: str):
    media = {"file": open(file_path, "rb")}
    url = settings.SITE_URL + "wp-json/wp/v2/media"
    response = session.post(url, files=media)
    featured_image_id = response.json().get("id")
    return featured_image_id


def upload_article(article: Article, session: requests.Session, categories_dict: dict):
    content_markdown = create_article_markdown(article)
    content_html = markdown_to_html(content_markdown)

    categorie_ids = [categories_dict[article.category]]

    post_data = {
        "title": article.title,
        "slug": article.url_ending,
        "content": content_html,
        "excerpt": article.excerpt,
        "categories": categorie_ids,
        "status": "private",
    }

    if article.image_generated:
        media_file_path = f"{settings.IMAGE_PATH}/{str(article.id)}.png"
        featured_image_id = upload_media(session, media_file_path)
        post_data["featured_media"] = featured_image_id

    responce, success = upload_article_request(session, post_data)

    if success:
        article.is_published = True
        article.save()
    else:
        logger.error("failed to upload article")
        logger.error(responce.json())

    return article, success
