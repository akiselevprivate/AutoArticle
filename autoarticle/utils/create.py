from settings.settings import settings
from settings.logger import logger
from utils.llm import llm_json_completion, llm_completion
from utils.other import chunks, replace_urls_in_markdown
import json
from copy import copy
import numpy as np
from db.models import Article, Action
import uuid as uuid_pkg


def create_titles(
    titles_count: int,
):
    titles_prompt = open(settings.TITLE_PROMPT_FILE, "r").read()
    title_examples_list = json.load(open(settings.JSON_TITLE_EXAMPLES_FILE, "r"))
    title_exaples_str = "\n".join(title_examples_list)
    replaced_prompt = (
        titles_prompt.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{examples}}", title_exaples_str)
        .replace(r"{{ammount}}", str(titles_count))
    )

    def test_dict_output(dict_completion):
        return len(dict_completion["titles"]) == settings.GEN_TITLES_COUNT

    try:
        titles_dict_list, used_tokens = llm_json_completion(
            [replaced_prompt], 2048, True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating titles ", e)
        raise Exception("error generating titles")
    titles_list = titles_dict_list[0]["titles"]
    return titles_list, used_tokens


def create_alternative_titles(titles: list):
    alt_titles_prompt = open(settings.ALTERNATIVE_TITLE_PROMPT_FILE, "r").read()
    titles_str = "\n".join(titles)
    replaced_prompt = (
        alt_titles_prompt.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{titles}}", titles_str)
        .replace(r"{{ammount}}", str(settings.GEN_TITLES_COUNT))
    )

    def test_dict_output(dict_completion):
        return len(dict_completion["titles"]) == settings.GEN_TITLES_COUNT

    try:
        alt_titles_dict_list, used_tokens = llm_json_completion(
            [replaced_prompt], 4096, True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating alternative titles " + e)
        raise Exception("error generating alternative titles")
    alt_titles_list = alt_titles_dict_list[0]["titles"]
    return alt_titles_list, used_tokens


def create_outlines(gen_titles: list, all_titles: list, all_titles_uuids: list):
    prompt_text = open(settings.OUTLINE_PROMPT_FILE, "r").read()
    section_prompts = []
    local_title_ids_list = []
    for title in gen_titles:
        all_titles_copy = copy(all_titles)
        del all_titles_copy[all_titles_copy.index(title)]
        np.random.shuffle(all_titles_copy)
        use_titles = all_titles_copy[: settings.LINKING_TITLES_IN_SECTION_COUNT]
        all_titles_with_id = [[idx + 1, title] for idx, title in enumerate(use_titles)]
        local_title_ids_list.append(all_titles_with_id)
        linking_articles_db_str_list = [
            f"{title_id}, {title}" for title_id, title in all_titles_with_id
        ]
        linking_articles_db_str = "\n".join(linking_articles_db_str_list)
        prompt = (
            prompt_text.replace(r"{{topic}}", settings.TOPIC)
            .replace(r"{{title}}", title)
            .replace(r"{{sections_ammount}}", str(settings.ARTICLE_SECTIONS_COUNT))
            .replace(r"{{linking_articles_database}}", linking_articles_db_str)
        )
        section_prompts.append(prompt)

    def dict_check(dict_completion: dict):
        return (
            all(
                [
                    i in ["outline", "categories", "tags"]
                    for i in list(dict_completion.keys())
                ]
            )
            and len(dict_completion["outline"]) == settings.ARTICLE_SECTIONS_COUNT
        )

    outlines_dict_list, used_tokens = llm_json_completion(
        section_prompts, 2048, False, dict_check
    )

    def find_index(array, target_value):
        for i, tuple in enumerate(array):
            if tuple[0] == target_value:
                return i
        return -1  # mega error

    for idx, (linking_id_title, o) in enumerate(
        zip(local_title_ids_list, outlines_dict_list)
    ):
        if o:
            for idx_y, (_, section_link_id) in enumerate(o["outline"]):
                id_index = find_index(linking_id_title, section_link_id)
                public_article_title = linking_id_title[id_index][1]
                title_idx = all_titles.index(public_article_title)
                section_article_uuid = all_titles_uuids[title_idx]
                outlines_dict_list[idx]["outline"][idx_y][1] = section_article_uuid

    return outlines_dict_list, used_tokens


def create_section_chunks(
    gen_titles: list, all_titles: list, all_titles_uuids: list, outlines: list
):
    prompt_text = open(settings.SECTION_PROMPT_FILE, "r").read()
    section_prompts = []
    for o, title in zip(outlines, gen_titles):
        if o:
            for s in o["outline"]:
                linking_article_title = all_titles[all_titles_uuids.index(s[1])]
                prompt = (
                    prompt_text.replace(r"{{title}}", title)
                    .replace(r"{{linking_article_title}}", linking_article_title)
                    .replace(r"{{section_title}}", s[0])
                )
                section_prompts.append(prompt)

    section_completions, used_tokens = llm_completion(section_prompts, 2048)

    sections_chunks = chunks(section_completions, settings.ARTICLE_SECTIONS_COUNT)

    all_sections_chunks = []
    for idx, o in enumerate(o):
        if o:
            sections = sections_chunks[idx]
        else:
            sections = None
        all_sections_chunks.append(sections)

    return all_sections_chunks, used_tokens


def get_existing_titles(article_type: str):
    articles = Article.select().where(
        Action.is_deleted == False
        and Article.is_complete == True
        and Article.article_type == article_type
    )
    titles = [a.title for a in articles]
    uuids = [str(a.id) for a in articles]
    return titles, uuids


def create_full_markdown(title: str, sections_list: dict, section_chunk: list):
    content_list = [
        f"# {title}",
    ]
    for (section_title, replace_url), section_md in zip(sections_list, section_chunk):
        content_list.append(f"## {section_title}")
        url_replaced_md = replace_urls_in_markdown(section_md, replace_url)
        content_list.append(url_replaced_md)

    markdown_string = "\n".join(content_list)
    return markdown_string
