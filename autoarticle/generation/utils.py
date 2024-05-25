from unidecode import unidecode
import re
import requests
from io import BytesIO
from PIL import Image
from settings.logger import logger
from db.models import Article, Section
from utils.other import LINK_PATTERN

import random


def generate_slug(text: str):
    # Convert to lowercase
    url = text.lower()

    # Remove special characters and replace spaces with hyphens
    url = "".join(c if c.isalnum() or c.isspace() else "" for c in unidecode(url))

    # Remove consecutive hyphens
    url = "-".join(url.strip().split(" "))

    url = url.replace("--", "-")

    return url


def extract_text_from_quotes(text: str):
    match = re.search(r'"(.*?)"', text)

    if match:
        return match.group(1)

    return text


def save_image_from_url(url, output_path):
    response = requests.get(url)

    if response.status_code == 200:
        # Open the image using PIL
        image = Image.open(BytesIO(response.content))

        # Save the image to the specified path
        image.save(output_path)

        logger.debug(f"Image saved to {output_path}")
        return True
    else:
        logger.error(
            f"Failed to retrieve the image. Status code: {response.status_code}"
        )
        return False


def get_sections(article_uuid: str):
    sections = (
        Section.select()
        .where(Section.article == article_uuid)
        .order_by(Section.idx.asc())
    )
    return sections


def anchor_matches(text: str):

    matches = re.findall(LINK_PATTERN, text)

    # Extract group 1 from each match
    anchor_matches = [match[0] for match in matches]

    return anchor_matches


def generate_random_bool_list(length: int, number_of_trues: int):
    if number_of_trues > length:
        number_of_trues = length
    bool_list = [False] * length
    true_indices = random.sample(
        range(length), number_of_trues
    )  # Select x random indices
    for index in true_indices:
        bool_list[index] = True
    return bool_list


def split_paragraphs(text):
    if "\n\n" in text:
        paragraphs = text.split("\n\n")
    elif "\n" in text:
        paragraphs = text.split("\n")
    else:
        paragraphs = text.splitlines()
    return paragraphs
