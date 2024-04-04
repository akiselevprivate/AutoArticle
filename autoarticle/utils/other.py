import json
import uuid as uuid_pkg
import commonmark
import re
import requests
from io import BytesIO
from PIL import Image
from settings.logger import logger


def extract_json(string: str) -> dict:
    json_string = string[string.find("{") : string.rfind("}") + 1]
    return json.loads(json_string)


LINK_PATTERN = r"\[([^\]]*)\]\((.*?)\)"


def replace_urls_in_markdown(input_string, new_url):

    def replace_func(match):
        if match.group(1) == "anchor":
            return "[link]({})".format(new_url)
        else:
            return "[{}]({})".format(match.group(1), new_url)

    replaced_string = re.sub(LINK_PATTERN, replace_func, input_string)

    return replaced_string


def markdown_to_html(markdown_str: str):
    html = commonmark.commonmark(markdown_str)
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


def count_words_in_markdown(markdown):
    text = markdown

    # Comments
    text = re.sub(r"<!--(.*?)-->", "", text, flags=re.MULTILINE)
    # Tabs to spaces
    text = text.replace("\t", "    ")
    # More than 1 space to 4 spaces
    text = re.sub(r"[ ]{2,}", "    ", text)
    # Footnotes
    text = re.sub(r"^\[[^]]*\][^(].*", "", text, flags=re.MULTILINE)
    # Indented blocks of code
    text = re.sub(r"^( {4,}[^-*]).*", "", text, flags=re.MULTILINE)
    # Custom header IDs
    text = re.sub(r"{#.*}", "", text)
    # Replace newlines with spaces for uniform handling
    text = text.replace("\n", " ")
    # Remove images
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    # Remove HTML tags
    text = re.sub(r"</?[^>]*>", "", text)
    # Remove special characters
    text = re.sub(r"[#*`~\-–^=<>+|/:]", "", text)
    # Remove footnote references
    text = re.sub(r"\[[0-9]*\]", "", text)
    # Remove enumerations
    text = re.sub(r"[0-9#]*\.", "", text)

    return len(text.split())
