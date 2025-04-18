import json
from settings.settings import settings


TITLE = open(settings.TITLE_PROMPT_FILE, "r").read()
TITLES = open(settings.TITLES_PROMPT_FILE, "r").read()
CATEGORIES = open(settings.CATEGORIES_PROMPT_FILE, "r").read()
OUTLINE = open(settings.OUTLINE_PROMPT_FILE, "r").read()
SECTION = open(settings.SECTION_PROMPT_FILE, "r").read()
ANCHOR = open(settings.ANCHORS_PROMPT_FILE, "r").read()
ADDITIONAL_DATA = open(settings.ADDITIONAL_DATA_PROMPT_FILE, "r").read()
DATA_SPLIT = open(settings.DATA_SPLIT_PROMPT_FILE, "r").read()
FAQ = open(settings.FAQ_PROMPT_FILE, "r").read()
PRODUCT_OUTLINE = open(settings.PRODUCT_OUTLINE_PROMPT_FILE, "r").read()

IMAGE_GENERATION = open(settings.IMAGE_GENERATION_PROMPT_FILE, "r").read()
IMAGE_DESCRIPTION = open(settings.IMAGE_DESCRIPTION_PROMPT_FILE, "r").read()
