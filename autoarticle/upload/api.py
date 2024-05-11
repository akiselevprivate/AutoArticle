import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from settings.settings import settings
from settings.logger import logger
from generation.utils import generate_slug
from upload.utils import create_image_tag


def create_session():
    session = requests.Session()
    session.auth = (settings.WP_USER, settings.WP_APPLICATION_PASSWORD)
    return session


def get_users(session: requests.Session):
    url = settings.SITE_URL + "wp-json/wp/v2/users"
    responce = session.get(url)
    return responce.json()


def upload_media(
    session: requests.Session, file_path: str, alt_text: str, user_id: int
):
    url = settings.SITE_URL + "wp-json/wp/v2/media"
    name = generate_slug(" ".join(alt_text.split(" ")[:10]))
    multipart_data = MultipartEncoder(
        fields={
            # a file upload field
            "file": (name + ".webp", open(file_path, "rb"), "image/webp"),
            # plain text fields
            "alt_text": alt_text,
            "author": str(user_id),
        }
    )
    response = session.post(
        url, data=multipart_data, headers={"Content-Type": multipart_data.content_type}
    )
    featured_image_id = response.json().get("id")
    # json.dump(response.json(), open("upload.json", "w+"))

    if featured_image_id == None:
        logger.error(response.json())
        raise Exception("failed to upload image")

    image_tag = create_image_tag(response.json())

    return featured_image_id, image_tag


def upload_article_request(session: requests.Session, article_data: dict):
    url = settings.SITE_URL + "wp-json/wp/v2/posts"
    responce = session.post(url, json=article_data)
    return responce, responce.status_code == 201


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
