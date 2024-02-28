import json
import uuid as uuid_pkg
from unidecode import unidecode
import markdown as markdown_pkg
import re
import requests
from io import BytesIO
from PIL import Image
from settings.logger import logger


def extract_json(string: str) -> dict:
    json_string = string[string.find("{") : string.rfind("}") + 1]
    return json.loads(json_string)


def create_uuid_list(count: int):
    return [str(uuid_pkg.uuid4()) for _ in range(count)]


def generate_seo_friendly_url(title: str):
    # Convert to lowercase
    url = title.lower()

    # Remove special characters and replace spaces with hyphens
    url = "".join(c if c.isalnum() or c.isspace() else "" for c in unidecode(url))

    # Remove consecutive hyphens
    url = "-".join(url.strip().split(" "))

    return url


def chunks(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def replace_urls_in_markdown(input_string, new_url):
    # Define a regular expression pattern to match the links and capture title and url separately
    pattern = r"\[([^\]]*)\]\((.*?)\)"

    # Use re.sub() to replace the matched URLs with the new_url
    replaced_string = re.sub(pattern, r"[\1]({})".format(new_url), input_string)

    return replaced_string


def markdown_to_html(markdown_str: str):
    html = markdown_pkg.markdown(markdown_str)
    return html


def remove_title_from_markdown(markdown_str: str):
    lines = markdown_str.split("\n")
    if lines[0].startswith("#"):
        del lines[0]

    result = "\n".join(lines)
    return result


def remove_first_h2_markdown(markdown_str: str):
    lines = markdown_str.split("\n")
    if lines[0].startswith("##"):
        del lines[0]

    result = "\n".join(lines)
    return result


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
