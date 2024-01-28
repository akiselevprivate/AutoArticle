import json
import uuid as uuid_pkg
from unidecode import unidecode
import re


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