from settings import prompts
from settings.settings import settings
from settings.logger import logger
from utils.llm import json_llm_completion, llm_completion
from generation.utils import anchor_matches

from settings.settings import settings


def generate_outline(
    title: str, sections_ammount: int, topic: str, category: str, article_data: str
) -> dict:
    prompt = (
        prompts.OUTLINE.replace(r"{title}", title)
        .replace(r"{sections_ammount}", str(sections_ammount))
        .replace(r"{data}", article_data)
        .replace(r"{topic}", topic)
        .replace(r"{category}", category)
    )

    def test_dict_output(dict_completion: dict):
        return (
            "outline" in dict_completion.keys()
            and len(dict_completion["outline"]) == sections_ammount
        )

    outline_dict, all_usages = json_llm_completion(
        prompt, 512, throw_exception=False, other_checks_func=test_dict_output
    )

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
    include_link: bool,
    anchor: str = None,
    link_title: str = None,
) -> str:

    link_req_prompt = """You (always) have to add the provided link.
Never put link in sub-headings or separate paragraphs.
Never add link sources."""
    base_link_prompt = (
        r'Additionally, within the content (not separately), you have too add a link to the article "{link_title}" using the anchor text "{anchor}" using this format [{anchor}](1).'
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
        prompts.SECTION.replace(r"{title}", title)
        .replace(r"{link_req}", link_req_prompt)
        .replace(r"{link_prompt}", link_prompt)
        .replace(r"{section_title}", section)
        .replace(r"{full_outline}", full_outline_text)
        .replace(r"{data}", article_data)
    )

    # open("prompt.txt", "w+").write(prompt)

    for _ in range(settings.MAX_SECTION_RETRIES):

        section_md, usage = llm_completion(
            prompt, 2048, temperature=0.8, frequency_penalty=0.3, presence_penalty=0.04
        )

        generated_anchors = anchor_matches(section_md)

        if not include_link:
            return section_md, generated_anchors

        # if len(generated_anchors) == 1 and generated_anchors[0] == anchor:
        if len(generated_anchors) >= 1:
            return section_md, generated_anchors
        else:
            print(anchor)
            logger.info("Regenerating section")

    logger.error(section_md)
    logger.error(str(generated_anchors))
    raise Exception("Retried multiple times.")
