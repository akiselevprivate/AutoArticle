from settings import prompts
from settings.settings import settings
from utils.llm import json_llm_completion
from settings.logger import logger


def generate_categories(topic: str, ammount: int) -> list[str]:
    prompt = prompts.CATEGORIES.replace(r"{topic}", topic).replace(
        r"{ammount}", str(ammount)
    )

    def test_dict_output(dict_completion):
        return (
            "categories" in dict_completion.keys()
            and len(dict_completion["categories"]) == ammount
        )

    try:
        categries_dict, all_usages = json_llm_completion(
            prompt, 300, "gpt-4-0125-preview", True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating categories ", e)
        raise Exception("error generating categories")
    categories = categries_dict["categories"]
    return categories


def generate_titles(topic: str, category: str, ammount: int) -> list[str]:
    prompt = (
        prompts.TITLES.replace(r"{category}", category)
        .replace(r"{topic}", settings.TOPIC)
        .replace(r"{ammount}", str(ammount))
    )

    def test_dict_output(dict_completion):
        return (
            "titles" in dict_completion.keys()
            and len(dict_completion["titles"]) == ammount
        )

    try:
        titles_dict, all_usages = json_llm_completion(
            prompt, 300, "gpt-4-0125-preview", True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating titles ", e)
        raise Exception("error generating titles")
    titles_list = titles_dict["titles"]
    return titles_list
