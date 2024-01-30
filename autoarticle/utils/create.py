from settings.settings import settings
from settings.logger import logger
from utils.llm import json_llm_completion, llm_completion
from db.models import Article, Action, ArticleLink


import json
from copy import copy
import numpy as np
import concurrent.futures
import asyncio


def create_titles(
    titles_count: int,
) -> [list, list]:
    titles_prompt = open(settings.TITLE_PROMPT_FILE, "r").read()
    title_examples_list = json.load(open(settings.JSON_TITLE_EXAMPLES_FILE, "r"))
    title_exaples_str = "\n".join(title_examples_list)
    replaced_prompt = (
        titles_prompt.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{examples}}", title_exaples_str)
        .replace(r"{{ammount}}", str(titles_count))
    )

    def test_dict_output(dict_completion):
        return "titles" in dict_completion.keys()
        # return len(dict_completion["titles"]) == settings.GEN_TITLES_COUNT

    try:
        titles_dict, all_usages = json_llm_completion(
            replaced_prompt, 2048, True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating titles ", e)
        raise Exception("error generating titles")
    titles_list = titles_dict["titles"]
    return titles_list, all_usages


def create_outline(title: list, linking_titles_with_uuids: list):
    prompt_text = open(settings.OUTLINE_PROMPT_FILE, "r").read()
    linking_titles_with_uuids_copy = copy(linking_titles_with_uuids)
    current_title_idx = [i[0] for i in linking_titles_with_uuids_copy].index(title)
    del linking_titles_with_uuids_copy[current_title_idx]
    np.random.shuffle(linking_titles_with_uuids_copy)
    linking_titles_with_uuids_copy = linking_titles_with_uuids_copy[
        : settings.LINKING_TITLES_IN_SECTION_COUNT
    ]
    linking_titles_with_local_id = [
        [idx + 1, title_with_uuid[0]]
        for idx, title_with_uuid in enumerate(linking_titles_with_uuids_copy)
    ]
    linking_articles_db_str_list = [
        f"{local_id}, {title}" for title, local_id in linking_titles_with_local_id
    ]
    linking_articles_db_str = "\n".join(linking_articles_db_str_list)
    prompt = (
        prompt_text.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{title}}", title)
        .replace(r"{{categories_ammount}}", str(settings.CATEGORIES_COUNT))
        .replace(r"{{faq_ammount}}", str(settings.FAQ_AMMOUNT))
        .replace(r"{{sections_ammount}}", str(settings.ARTICLE_SECTIONS_COUNT))
        .replace(r"{{linking_articles_database}}", linking_articles_db_str)
    )

    def dict_check(dict_completion: dict):
        return (
            all(
                [
                    i in ["outline", "categories", "faq", "excerpt"]
                    for i in list(dict_completion.keys())
                ]
            )
            and len(dict_completion["outline"]) == settings.ARTICLE_SECTIONS_COUNT
        )

    outline_dict, usage = json_llm_completion(prompt, 2048, False, dict_check)

    def find_index(array, target_value):
        for i, tuple in enumerate(array):
            if tuple[0] == target_value:
                return i
        return -1  # mega error

    if outline_dict:
        for idx, (_, section_link_id) in enumerate(outline_dict["outline"]):
            id_index = find_index(linking_titles_with_local_id, section_link_id)
            public_article_title = linking_titles_with_local_id[id_index][1]
            title_idx = [i[1] for i in linking_titles_with_local_id].index(
                public_article_title
            )
            section_article_uuid = linking_titles_with_uuids_copy[title_idx][0]
            outline_dict["outline"][idx][1] = section_article_uuid

    return outline_dict, usage


async def create_sections_markdown(
    title: str, linking_titles_with_uuids: list, outline_dict: dict
):
    prompt_text = open(settings.SECTION_PROMPT_FILE, "r").read()
    section_prompts = []
    linking_titles = [i[0] for i in linking_titles_with_uuids]
    linking_uuids = [i[0] for i in linking_titles_with_uuids]
    for section in outline_dict["outline"]:
        linking_article_title = linking_titles[linking_uuids.index(section[1])]
        prompt = (
            prompt_text.replace(r"{{title}}", title)
            .replace(r"{{linking_article_title}}", linking_article_title)
            .replace(r"{{section_title}}", section[0])
        )
        section_prompts.append(prompt)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, llm_completion, *[prompt, 2048])
            for prompt in section_prompts
        ]
        results = await asyncio.gather(*tasks)

    completions, all_usage = np.array(results).T.copy().tolist()

    return completions, all_usage


async def continue_article(article: Article, linking_titles_with_uuids: list):
    title = article.title
    success = True
    if not article.outline_json:
        outline_dict, outline_usage_list = create_outline(
            title, linking_titles_with_uuids
        )
        if not outline_dict:
            success = False
        else:
            article.outline_json = json.dumps(outline_dict)
            article.categories_json = json.dumps(outline_dict["categories"])
            article.faq_json = json.dumps(outline_dict["faq"])
            article.excerpt = outline_dict["excerpt"]
            article.save()

            for _, linking_article_uuid in outline_dict["outline"]:
                ArticleLink.create(
                    from_article=article, to_article=linking_article_uuid
                )
                if str(article.id) == linking_article_uuid:
                    logger.error(f"linking thesame article: {linking_article_uuid}")

    else:
        outline_dict = json.loads(article.outline_json)

    if success and not article.sections_list_json:
        sections_dict_list, sections_usage_list = await create_sections_markdown(
            title, linking_titles_with_uuids, outline_dict
        )
        article.sections_list_json = json.dumps(sections_dict_list)
        article.save()
    else:
        sections_dict_list = json.loads(article.sections_list_json)

    article.is_complete = True
    article.is_succesful = success
    article.save()

    return article, success


def get_existing_titles_with_uuid(article_type: str):
    articles = (
        Article.select()
        .join(Action)
        .where(
            Action.action_deleted == False,
            Article.is_complete == True,
            Article.is_succesful == True,
            Article.article_type == article_type,
            Article.article_deleted == False,
        )
    )
    titles_with_uuid = [[a.title, str(a.id)] for a in articles]
    return titles_with_uuid
