import json
import uuid as uuid_pkg
import commonmark
import re
import requests
from io import BytesIO
from PIL import Image
from settings.logger import logger

from bs4 import BeautifulSoup


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


def remove_duplicate_h3(markdown_str: str, section_title: str):
    lines = markdown_str.split("\n")
    if lines[0].startswith("###") and lines[0][:3].strip() == section_title.strip():
        del lines[0]

    result = "\n".join(lines)
    return result


def remove_first_h3(markdown_str: str):
    lines = markdown_str.split("\n")
    if lines[0].startswith("###"):
        del lines[0]

    result = "\n".join(lines)
    return result


def clean_markdown(markdown: str):
    # Comments
    markdown = re.sub(r"<!--(.*?)-->", "", markdown, flags=re.MULTILINE)
    # Tabs to spaces
    markdown = markdown.replace("\t", "    ")
    # More than 1 space to 4 spaces
    markdown = re.sub(r"[ ]{2,}", "    ", markdown)
    # Footnotes
    markdown = re.sub(r"^\[[^]]*\][^(].*", "", markdown, flags=re.MULTILINE)
    # Indented blocks of code
    markdown = re.sub(r"^( {4,}[^-*]).*", "", markdown, flags=re.MULTILINE)
    # Custom header IDs
    markdown = re.sub(r"{#.*}", "", markdown)
    # Replace newlines with spaces for uniform handling
    markdown = markdown.replace("\n", " ")
    # Remove images
    markdown = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", markdown)
    # Remove HTML tags
    markdown = re.sub(r"</?[^>]*>", "", markdown)
    # Remove special characters
    markdown = re.sub(r"[#*`~\-–^=<>+|/:]", "", markdown)
    # Remove footnote references
    markdown = re.sub(r"\[[0-9]*\]", "", markdown)
    # Remove enumerations
    markdown = re.sub(r"[0-9#]*\.", "", markdown)

    return markdown


def count_words_in_markdown(markdown: str):
    clean = clean_markdown(markdown)

    return len(clean.split())


def markdown_to_text(markdown_string):
    """Converts a markdown string to plaintext"""

    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown_to_html(markdown_string)

    # remove code snippets
    html = re.sub(r"<pre>(.*?)</pre>", " ", html)
    html = re.sub(r"<code>(.*?)</code >", " ", html)

    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = "".join(soup.findAll(string=True))

    return re.sub(r"\[\d+\]", "", text)


def batch(input_list: list, n: int):
    # Calculate the size of each batch
    batch_size = len(input_list) // n
    # Initialize the list of batches
    batches = []
    # Split the input list into batches
    for i in range(0, len(input_list), batch_size):
        batches.append(input_list[i : i + batch_size])
    return batches
