from settings import prompts
from settings.settings import settings
from utils.llm import llm_completion
from utils.image_gen import generate_image, generate_upscale, compress_convert_image
from generation.utils import extract_text_from_quotes, save_image_from_url
import os
import uuid as uuid_pkg


def generate_hero_prompt(title: str):
    prompt = prompts.IMAGE_DESCRIPTION.replace(r"{title}", title).replace(
        r"{additional}", ""
    )
    completion, usage = llm_completion(prompt, 100)
    image_description = extract_text_from_quotes(completion)
    return image_description


def generate_section_prompt(title: str, section: str):
    additional = f' paragraph titled: "{section}"'
    prompt = prompts.IMAGE_DESCRIPTION.replace(r"{title}", title).replace(
        r"{additional}", additional
    )
    completion, usage = llm_completion(prompt, 100)
    image_description = extract_text_from_quotes(completion)
    return image_description


def generate_hero_image_from_prompt(image_description: str):
    uuid = uuid_pkg.uuid4()
    raw_image_url = generate_image(image_description)
    upscale_image_url = generate_upscale(raw_image_url)
    raw_save_file_path = f"{settings.IMAGE_PATH}/{uuid}-scaled.png"
    success = save_image_from_url(upscale_image_url, raw_save_file_path)
    final_save_file_path = f"{settings.IMAGE_PATH}/{uuid}.webp"
    compress_convert_image(raw_save_file_path, final_save_file_path)
    os.remove(raw_save_file_path)
    return uuid
