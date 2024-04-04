from settings import prompts
from settings.settings import settings
from utils.llm import llm_completion
from utils.image_gen import generate_image, generate_upscale, compress_convert_image
from generation.utils import extract_text_from_quotes, save_image_from_url
import os


def generate_hero_image(title: str, uuid: str):
    prompt = prompts.IMAGE_DESCRIPTION.replace(r"{title}", title)
    completion, usage = llm_completion(prompt, 100)
    image_description = extract_text_from_quotes(completion)
    raw_image_url = generate_image(image_description)
    upscale_image_url = generate_upscale(raw_image_url)
    raw_save_file_path = f"{settings.IMAGE_PATH}/{uuid}-scaled.png"
    success = save_image_from_url(upscale_image_url, raw_save_file_path)
    final_save_file_path = f"{settings.IMAGE_PATH}/{uuid}.webp"
    compress_convert_image(raw_save_file_path, final_save_file_path)
    os.remove(raw_save_file_path)
    return image_description
