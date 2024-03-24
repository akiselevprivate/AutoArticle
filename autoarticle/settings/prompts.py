import json
from settings.settings import settings


TITLES = open(settings.TITLE_PROMPT_FILE, "r").read()
CATEGORIES = open(settings.CATEGORIES_PROMPT_FILE, "r").read()
OUTLINE = open(settings.OUTLINE_PROMPT_FILE, "r").read()
SECTION = open(settings.SECTION_PROMPT_FILE, "r").read()

IMAGE_GENERATION = open(settings.IMAGE_GENERATION_PROMPT_FILE, "r").read()
IMAGE_DESCRIPTION = open(settings.IMAGE_DESCRIPTION_PROMPT_FILE, "r").read()
