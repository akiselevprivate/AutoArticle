from settings import prompts
from settings.settings import settings
from settings.logger import logger
from utils.llm import json_llm_completion, llm_completion
from generation.utils import anchor_matches

from settings.settings import settings


def generate_outline(title: str, sections_ammount: int) -> dict:
    prompt = prompts.OUTLINE.replace(r"{title}", title).replace(
        r"{sections_ammount}", str(sections_ammount)
    )

    def test_dict_output(dict_completion: dict):
        return (
            "outline" in dict_completion.keys()
            and len(dict_completion["outline"]) == sections_ammount
        )

    outline_dict, all_usages = json_llm_completion(
        prompt, 1024, throw_exception=False, other_checks_func=test_dict_output
    )

    return outline_dict


def create_text_section_outline(section_titles: list[str]) -> str:
    full_outline_text_list = []
    for title in section_titles:
        full_outline_text_list.append(f"## {title}")
    full_outline_text = "\n".join(full_outline_text_list)
    return full_outline_text


def generate_section(
    title: str,
    section: str,
    anchor: str,
    link_title: str,
    section_titles: list[str],
) -> str:
    full_outline_text = create_text_section_outline(section_titles)
    prompt = (
        prompts.SECTION.replace(r"{title}", title)
        .replace(r"{anchor}", anchor)
        .replace(r"{link_title}", link_title)
        .replace(r"{section_title}", section)
        .replace(r"{full_outline}", full_outline_text)
    )

    for _ in range(settings.MAX_SECTION_RETRIES):

        section_md, usage = llm_completion(
            prompt, 2048, temperature=0.8, frequency_penalty=0.15, presence_penalty=0.04
        )

        generated_anchors = anchor_matches(section_md)

        if len(generated_anchors) <= 1:
            return section_md, generated_anchors
        else:
            logger.error("generation > 1 link")

    logger.error(section_md)
    logger.error(str(generated_anchors))
    raise Exception("Retried multiple times, more than one link in section.")
