from unidecode import unidecode
import re
import requests
from io import BytesIO
from PIL import Image
from settings.logger import logger


def generate_slug(text: str):
    # Convert to lowercase
    url = text.lower()

    # Remove special characters and replace spaces with hyphens
    url = "".join(c if c.isalnum() or c.isspace() else "" for c in unidecode(url))

    # Remove consecutive hyphens
    url = "-".join(url.strip().split(" "))

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
