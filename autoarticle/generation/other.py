from settings import prompts
from settings.settings import settings
from utils.llm import json_llm_completion
from utils.perplexity import perplexity_llm
from settings.logger import logger
from generation.utils import split_paragraphs


def generate_categories(topic: str, ammount: int) -> list[str]:
    prompt = prompts.CATEGORIES.replace(r"{topic}", topic).replace(
        r"{ammount}", str(ammount)
    )

    def test_dict_output(dict_completion):
        return (
            "categories" in dict_completion.keys()
            and len(dict_completion["categories"]) >= ammount
        )

    try:
        categries_dict, all_usages = json_llm_completion(
            prompt, 300, throw_exception=True, other_checks_func=test_dict_output
        )
    except Exception as e:
        logger.error("error generating categories ", e)
        raise Exception("error generating categories")
    categories = categries_dict["categories"][:ammount]
    return categories


def generate_titles(topic: str, category: str, ammount: int) -> list[str]:
    prompt = (
        prompts.TITLES.replace(r"{category}", category)
        .replace(r"{topic}", topic)
        .replace(r"{ammount}", str(ammount))
    )

    def test_dict_output(dict_completion):
        return (
            "titles" in dict_completion.keys()
            and len(dict_completion["titles"]) >= ammount
        )

    try:
        titles_dict, all_usages = json_llm_completion(
            prompt, 300, throw_exception=True, other_checks_func=test_dict_output
        )
    except Exception as e:
        logger.error("error generating titles ", e)
        raise Exception("error generating titles")
    titles_list = titles_dict["titles"][:ammount]
    return titles_list


def generate_title(topic: str, category: str, tag: str):
    prompt = (
        prompts.TITLE.replace(r"{category}", category)
        .replace(r"{topic}", topic)
        .replace(r"{tag}", tag)
    )

    def test_dict_output(dict_completion: dict):
        return all([v in dict_completion.keys() for v in ["title", "search_query"]])

    try:
        title_dict, all_usages = json_llm_completion(
            prompt, 120, throw_exception=True, other_checks_func=test_dict_output
        )
    except Exception as e:
        logger.error("error generating title", e)
        raise Exception("error generating title")

    return title_dict["title"], title_dict["search_query"]


def generate_anchors(title: str, ammount: int, existing_anchors: list[str]):

    prompt = prompts.ANCHOR.replace(r"{title}", title).replace(
        r"{ammount}", str(ammount)
    )

    def test_dict_output(dict_completion):
        return (
            "anchors" in dict_completion.keys()
            and len(dict_completion["anchors"]) >= ammount
        )

    for _ in range(settings.MAX_ANCHOR_RETRIES):

        anchors_dict, all_usages = json_llm_completion(
            prompt, 500, other_checks_func=test_dict_output
        )

        anchors = anchors_dict["anchors"]

        unique_anchors = [a for a in anchors if a not in existing_anchors]

        if len(unique_anchors) >= ammount:
            return unique_anchors

    raise Exception("To many retries for unique anchors")


def generate_addiional_data(title: str):
    prompt = prompts.ADDITIONAL_DATA.replace(r"{query}", title)
    completion, usage = perplexity_llm(prompt, 300)

    # open("data.txt", "w+").write(completion)

    return completion


def generate_split_data(title: str, data: str, ammount: int, section_titles: list):

    # split_data = split_paragraphs(data)

    # if len(split_data) == ammount:
    #     return split_data

    outline_text = "\n".join(section_titles)

    prompt = (
        prompts.DATA_SPLIT.replace(r"{title}", title)
        .replace(r"{data}", data)
        .replace(r"{ammount}", str(ammount))
        .replace(r"{sections}", outline_text)
    )

    def test_dict_output(dict_completion):
        return (
            "paragraphs" in dict_completion.keys()
            and len(dict_completion["paragraphs"]) == ammount
        )

    paragraphs_dict, all_usages = json_llm_completion(
        prompt,
        1200,
        throw_exception=True,
        other_checks_func=test_dict_output,
    )

    return paragraphs_dict["paragraphs"]
