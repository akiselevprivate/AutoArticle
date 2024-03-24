from settings import prompts
from settings.settings import settings
from utils.llm import llm_completion
from utils.image_gen import generate_image
from generation.utils import extract_text_from_quotes, save_image_from_url


def generate_hero_image(title: str, uuid: str):
    prompt = prompts.IMAGE_DESCRIPTION.replace(r"{title}", title)
    completion, usage = llm_completion(prompt, 50)
    image_description = extract_text_from_quotes(completion)
    image_url = generate_image(image_description)
    save_file_path = f"{settings.IMAGE_PATH}/{uuid}.png"
    success = save_image_from_url(image_url, save_file_path)
    return image_description
