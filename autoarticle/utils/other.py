import json
import uuid as uuid_pkg
import markdown as markdown_pkg
import re
import requests
from io import BytesIO
from PIL import Image
from settings.logger import logger


def extract_json(string: str) -> dict:
    json_string = string[string.find("{") : string.rfind("}") + 1]
    return json.loads(json_string)


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
