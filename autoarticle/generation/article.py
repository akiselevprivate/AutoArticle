from settings import prompts
from settings.settings import settings
from settings.logger import logger
from utils.llm import json_llm_completion, llm_completion
from generation.utils import anchor_matches

from settings.settings import settings
from settings import content

import json


def generate_outline(
    title: str,
    sections_ammount: int,
    topic: str,
    category: str,
    article_data: str,
    article_type: str,
    tone: str,
    content_type: str,
) -> dict:

    if article_data:
        base_prompt = prompts.OUTLINE.replace(r"{data_split}", "").replace(
            r"{data}", article_data
        )
    else:
        base_prompt = prompts.OUTLINE.split(r"{data_split}")[1]

    if content_type == "PRODUCT_COMPARISON":
        outline_text = "first and the last sections of the article, make them questions not related to specific products."
    else:
        outline_text = "article"

    # outline_text = "article"  # TODO

    prompt = (
        base_prompt.replace(r"{title}", title)
        .replace(r"{outline_text}", outline_text)
        .replace(r"{sections_ammount}", str(sections_ammount))
        .replace(r"{topic}", topic)
        .replace(r"{category}", category)
        .replace(r"{type}", article_type)
        .replace(r"{tone}", tone)
    )

    def test_dict_output(dict_completion: dict):
        return (
            all(
                [
                    v in dict_completion.keys()
                    for v in ["outline", "excerpt", "video_query"]
                ]
            )
            and len(dict_completion["outline"]) == sections_ammount
        )

    outline_dict, all_usages = json_llm_completion(
        prompt, 512, throw_exception=False, other_checks_func=test_dict_output
    )

    # json.dump(outline_dict, open("dump.json", "w+"))

    return outline_dict


def create_text_section_outline(section_titles: list[str]) -> str:
    # full_outline_text_list = []
    # for title in section_titles:
    #     full_outline_text_list.append(f"## {title}")
    full_outline_text = "\n".join(section_titles)
    return full_outline_text


def generate_section(
    title: str,
    section: str,
    section_titles: list[str],
    article_data: str,
    article_type: str,
    tone: str,
    include_link: bool,
    word_count: int,
    anchor: str = None,
    link_title: str = None,
) -> str:

    if article_data:
        base_prompt = prompts.SECTION.replace(r"{data_split}", "").replace(
            r"{data}", article_data
        )

    else:
        base_prompt = prompts.SECTION.split(r"{data_split}")[1]

    link_req_prompt = """You (always) have to add the provided link inside other text to add information.
Never add link separately.
"""
    base_link_prompt = (
        r'As part of the text to add information you have too add a link to the article "{link_title}" using this format [{anchor}](1).'
        + "\n"
    )
    if include_link:
        link_prompt = base_link_prompt.replace(r"{anchor}", anchor).replace(
            r"{link_title}", link_title
        )
    else:
        link_req_prompt = ""
        link_prompt = ""

    full_outline_text = create_text_section_outline(section_titles)
    prompt = (
        base_prompt.replace(r"{title}", title)
        .replace(r"{link_req}", link_req_prompt)
        .replace(r"{link_prompt}", link_prompt)
        .replace(r"{section_title}", section)
        .replace(r"{type}", article_type)
        .replace(r"{full_outline}", full_outline_text)
        .replace(r"{tone}", tone)
        .replace(r"{word_count}", str(word_count))
    )

    # open("prompt.txt", "w+").write(prompt)

    for _ in range(settings.MAX_SECTION_RETRIES):

        section_md, usage = llm_completion(
            prompt, 2048, temperature=0.8, frequency_penalty=0.3, presence_penalty=0.04
        )

        generated_anchors = anchor_matches(section_md)

        if not include_link:
            return section_md, generated_anchors

        if len(generated_anchors) == 1 and generated_anchors[0] == anchor:
            # if len(generated_anchors) >= 1:
            return section_md, generated_anchors
        else:
            logger.info("Regenerating section")

    logger.error(section_md)
    logger.error(str(generated_anchors))
    logger.error("Retried section multiple times.")

    return section_md, generated_anchors
