from settings import prompts
from settings.settings import settings
from settings.logger import logger
from utils.llm import json_llm_completion, llm_completion


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
    title: str, section: str, linking_title: str, section_titles: list[str]
) -> str:
    full_outline_text = create_text_section_outline(section_titles)
    print(title)
    prompt = (
        prompts.SECTION.replace(r"{title}", title)
        .replace(r"{linking_article_title}", linking_title)
        .replace(r"{section_title}", section)
        .replace(r"{full_outline}", full_outline_text)
    )

    section_md, usage = llm_completion(prompt, 2048)

    return section_md
