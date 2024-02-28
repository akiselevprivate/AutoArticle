import json
from settings.settings import settings


TITLES = open(settings.TITLE_PROMPT_FILE, "r").read()
TITLE_EXAMPLES = json.load(open(settings.JSON_TITLE_EXAMPLES_FILE, "r"))
OUTLINE = open(settings.OUTLINE_PROMPT_FILE, "r").read()
# FAQ_EXAMPLES = json.load(open(settings.JSON_FAQ_EXAMPLES_FILE, "r"))
SECTION = open(settings.SECTION_PROMPT_FILE, "r").read()
CATEGORIES = open(settings.CATEGORIES_PROMPT_FILE, "r").read()
SITEMAP_EXTRACTION_PROMPT_FILE = open(
    settings.SITEMAP_EXTRACTION_PROMPT_FILE, "r"
).read()

IMAGE_GENERATION = open(settings.IMAGE_GENERATION_PROMPT_FILE, "r").read()
IMAGE_DESCRIPTION = open(settings.IMAGE_DESCRIPTION_PROMPT_FILE, "r").read()

INTERLINKING = open(settings.INTERLINKING_PROMPT_FILE, "r").read()
