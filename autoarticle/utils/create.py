from settings.settings import settings
from settings.logger import logger
from utils.llm import json_llm_completion, llm_completion
from db.models import Article, Action, ArticleLink, Categorie
from settings import prompts
from utils.other import (
    generate_seo_friendly_url,
    extract_text_from_quotes,
    save_image_from_url,
)
from utils.image_gen import generate_image

import json
from copy import deepcopy, copy
import numpy as np
import concurrent.futures
import asyncio
from typing import Union, List


def save_new_articles(action: Action, titles: list):
    articles = []

    for title in titles:
        url_ending = generate_seo_friendly_url(title)
        try:
            article = Article.create(
                action=action,
                article_type=settings.ARTICLE_TYPE,
                title=title,
                url_ending=url_ending,
            )
            articles.append(article)
        except Exception as e:
            logger.info(e)
            logger.info(f'article with title: "{title}" already exists')

    return articles


def create_titles(titles_count: int, existing_titles: list) -> Union[list, list]:

    if (
        settings.ROTATE_EXAMPLE_TITLES
        and len(existing_titles) <= settings.ROTATING_EXAMPLE_TITLES_COUNT
    ):
        np.random.shuffle(existing_titles)
        rotated_titles = existing_titles[: settings.ROTATING_EXAMPLE_TITLES_COUNT]
        title_exaples_str = "\n".join(rotated_titles)
    else:
        title_exaples_str = "\n".join(prompts.TITLE_EXAMPLES)

    replaced_prompt = (
        prompts.TITLES.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{examples}}", title_exaples_str)
        .replace(r"{{additional_settings}}", settings.ADDITIONAL_TITLE_SETTINGS)
        .replace(r"{{ammount}}", str(titles_count))
    )

    def test_dict_output(dict_completion):
        return "titles" in dict_completion.keys()
        # return len(dict_completion["titles"]) == settings.GEN_TITLES_COUNT

    try:
        titles_dict, all_usages = json_llm_completion(
            replaced_prompt, 2048, "gpt-4-0125-preview", True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating titles ", e)
        raise Exception("error generating titles")
    titles_list = titles_dict["titles"]
    return titles_list, all_usages


def find_title(array, target_value):
    for local_id, title in array:
        if local_id == target_value:
            return title


def create_outline(title: str, categories: list):

    # faq_examples_str = "\n".join(prompts.FAQ_EXAMPLES)

    categories_with_local_id = [
        [idx + 1, categorie] for idx, categorie in enumerate(categories)
    ]
    categrories_db_str_list = [
        f"{local_id}, {categorie}" for local_id, categorie in categories_with_local_id
    ]
    categrories_db_str = "\n".join(categrories_db_str_list)

    prompt = (
        prompts.OUTLINE.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{title}}", title)
        # .replace(r"{{categories_ammount}}", str(settings.CATEGORIES_COUNT))
        # .replace(r"{{faq_ammount}}", str(settings.FAQ_AMMOUNT))
        # .replace(r"{{faq_examples}}", faq_examples_str)
        .replace(r"{{sections_ammount}}", str(settings.ARTICLE_SECTIONS_COUNT))
        .replace(r"{{categories_database}}", categrories_db_str)
    )

    def dict_check(dict_completion: dict):
        return (
            set(["outline", "category", "excerpt"]) == set(dict_completion.keys())
            # and all(
            #     [
            #         type(section["linking_id"]) == int
            #         and section["linking_id"] > 0
            #         and section["linking_id"]
            #         <= settings.LINKING_TITLES_IN_SECTION_COUNT
            #         for section in dict_completion["outline"]
            #     ]
            # )
            and len(dict_completion["outline"]) == settings.ARTICLE_SECTIONS_COUNT
        )

    outline_dict, usage_list = json_llm_completion(
        prompt, 1024, throw_exception=False, other_checks_func=dict_check
    )

    # json.dump(outline_dict, open("od.json", "w+"))

    if outline_dict:
        # print(categories_with_local_id)
        category = find_title(categories_with_local_id, int(outline_dict["category"]))
        # print(category)
        outline_dict["category"] = category

    # json.dump(outline_dict, open("res.json", "w+"))

    return outline_dict, usage_list


def create_linking(
    title: str,
    outline_dict: dict,
    linking_titles_with_uuids: list,
):
    linking_titles_with_uuids_copy = deepcopy(linking_titles_with_uuids)
    current_title_idx = [i[0] for i in linking_titles_with_uuids_copy].index(title)
    del linking_titles_with_uuids_copy[current_title_idx]
    np.random.shuffle(linking_titles_with_uuids_copy)
    linking_titles_with_uuids_copy = linking_titles_with_uuids_copy[
        : settings.LINKING_TITLES_COUNT
    ]
    linking_titles_with_local_id = [
        [idx + 1, title_with_uuid[0]]
        for idx, title_with_uuid in enumerate(linking_titles_with_uuids_copy)
    ]
    linking_articles_db_str_list = [
        f"{local_id}, {title}" for local_id, title in linking_titles_with_local_id
    ]
    linking_articles_db_str = "\n".join(linking_articles_db_str_list)

    full_outline_text = create_text_outline(outline_dict, False)

    prompt = (
        prompts.INTERLINKING.replace(
            r"{sections_count}", str(settings.ARTICLE_SECTIONS_COUNT)
        )
        .replace(r"{linking_articles_database}", linking_articles_db_str)
        .replace(r"{article_outline}", full_outline_text)
    )

    def dict_check(dict_completion: dict):
        return (
            "links" in dict_completion
            and len(dict_completion["links"]) == settings.ARTICLE_SECTIONS_COUNT
            and all(
                [i <= settings.LINKING_TITLES_COUNT for i in dict_completion["links"]]
            )
        )

    completion, usage = json_llm_completion(prompt, 1024, other_checks_func=dict_check)

    # json.dump(completion, open("aa.json", "w+"))

    linking_ids = completion["links"]

    linking_articles_uuids = []
    for section_link_id in linking_ids:
        public_article_title = find_title(linking_titles_with_local_id, section_link_id)
        title_idx = [i[1] for i in linking_titles_with_local_id].index(
            public_article_title
        )
        section_article_uuid = linking_titles_with_uuids_copy[title_idx][1]
        linking_articles_uuids.append(section_article_uuid)

    return linking_articles_uuids


def create_text_outline(outline_dict: dict, sub_outline: bool = True):
    full_outline_text_list = []
    for section in outline_dict["outline"]:
        full_outline_text_list.append(f"## {section['title']}")
        if sub_outline:
            for sub_heading in section["sub_headings"]:
                full_outline_text_list.append(f"## {sub_heading}")
    full_outline_text = "\n".join(full_outline_text_list)
    return full_outline_text


async def create_sections_markdown(
    title: str,
    linking_articles_uuids: list,
    linking_titles_with_uuids: list,
    outline_dict: dict,
):
    section_prompts = []
    linking_titles = [i[0] for i in linking_titles_with_uuids]
    linking_uuids = [i[1] for i in linking_titles_with_uuids]

    full_outline_text = create_text_outline(outline_dict, False)

    for section, linking_uuid in zip(outline_dict["outline"], linking_articles_uuids):
        linking_article_title = linking_titles[linking_uuids.index(linking_uuid)]
        prompt = (
            prompts.SECTION.replace(r"{{title}}", title)
            .replace(r"{{linking_article_title}}", linking_article_title)
            .replace(r"{{section_title}}", section["title"])
            .replace(r"{{full_outline}}", full_outline_text)
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


async def continue_article(
    article: Article, linking_titles_with_uuids: list, categories: list
):
    title = article.title
    success = True
    if not article.outline_json:
        outline_dict, outline_usage_list = create_outline(title, categories)
        if outline_dict == None:
            success = False
        else:
            article.outline_json = json.dumps(outline_dict)
            article.category = outline_dict["category"]
            article.excerpt = outline_dict["excerpt"]
            article.outline_tokens_used = sum(
                [usage.total_tokens for usage in outline_usage_list]
            )
            article.save()

    else:
        outline_dict = json.loads(article.outline_json)

    if success and not article.interlinking_uuids_json:
        linking_articles_uuids = create_linking(
            title, outline_dict, linking_titles_with_uuids
        )
        article.interlinking_uuids_json = json.dumps(linking_articles_uuids)
        article.save()

        for linking_uuid in linking_articles_uuids:
            ArticleLink.create(from_article=article, to_article=linking_uuid)
            if str(article.id) == linking_uuid:
                logger.error(f"linking thesame article: {linking_uuid}")

    else:
        linking_articles_uuids = json.loads(article.interlinking_uuids_json)

    if settings.GENERATE_IMAGE and success and not article.image_generated:
        success, image_description = create_image_from_title(
            article.title, str(article.id)
        )
        article.image_description = image_description
        article.image_generated = success
        article.save()

    if success and not article.sections_list_json:
        sections_dict_list, sections_usage_list = await create_sections_markdown(
            title, linking_articles_uuids, linking_titles_with_uuids, outline_dict
        )
        article.sections_list_json = json.dumps(sections_dict_list)
        article.sections_tokens_used = sum(
            [usage.total_tokens for usage in sections_usage_list]
        )
        article.save()
    else:
        sections_dict_list = json.loads(article.sections_list_json)

    article.is_complete = True
    article.is_succesful = success
    article.save()

    logger.info(f"completed article: {article.title}, success: {success}")

    return article, success


def get_existing_titles_with_uuid(article_type: str):
    articles = (
        Article.select()
        .join(Action)
        .where(
            Article.is_complete == True,
            Article.is_succesful == True,
            Article.article_type == article_type,
        )
    )
    titles_with_uuid = [[a.title, str(a.id)] for a in articles]
    return titles_with_uuid


def get_existing_categories():
    categories = Categorie.select()
    categories_terms = [c.term for c in categories]
    return categories_terms


def create_categories(
    count: int, existing_categories: list, titles: list
) -> List[Categorie]:
    existing_categories_str = "\n".join(existing_categories)
    titles_str = "\n".join(titles[: settings.CATEGORIE_TITLES_COUNT])
    replaced_prompt = (
        prompts.CATEGORIES.replace(r"{{topic}}", settings.TOPIC)
        .replace(r"{{count}}", str(count))
        .replace(r"{{titles}}", titles_str)
        .replace(r"{{existing_categories}}", existing_categories_str)
    )

    def test_dict_output(dict_completion):
        return (
            "categories" in dict_completion.keys()
            and len(dict_completion["categories"]) >= count
        )

    try:
        categories_dict_list, all_usages = json_llm_completion(
            replaced_prompt, 1024, "gpt-4-0125-preview", True, test_dict_output
        )
    except Exception as e:
        logger.error("error generating categories ", e)
        raise Exception("error generating categories")
    categories_list = categories_dict_list["categories"][:count]

    categorie_db_list = []
    for cat in categories_list:
        try:
            db_cat = Categorie.create(term=cat)
            categorie_db_list.append(cat)
        except:
            logger.error(f"Categorie {cat} already existis")

    logger.info(f"Created {len(categorie_db_list)} new categories.")

    return categorie_db_list, all_usages


def get_and_add_categories(titles: list):
    existing_categories = get_existing_categories()
    if len(existing_categories) < settings.CATEGORIES_COUNT:
        categories_terms = [c[0] for c in existing_categories]
        titles_str = "\n".join(titles)
        new_categories, usage = create_categories(
            settings.CATEGORIES_COUNT - len(existing_categories),
            categories_terms,
            titles_str,
        )
        existing_categories += new_categories
    return existing_categories


# def process_articles_in_paralel(articles: list[Article], linking_titles_with_uuids):
#     loop = asyncio.get_event_loop()

#     tasks = [
#         continue_article(article, linking_titles_with_uuids) for article in articles
#     ]

#     # Run the asynchronous functions in the event loop
#     results = loop.run_until_complete(asyncio.gather(*tasks))

#     loop.close()

#     finished_articles = [i[0] for i in results]
#     success_list = [i[1] for i in results]

#     return finished_articles, success_list


def process_articles_sequentialy(
    articles: list[Article],
    linking_titles_with_uuids: list,
    categories: list,
):
    finished_articles, success_list = [], []

    for article in articles:
        finished_article, is_successfull = asyncio.run(
            continue_article(article, linking_titles_with_uuids, categories)
        )
        finished_articles.append(finished_article)
        success_list.append(is_successfull)

    return finished_articles, success_list


def create_image_from_title(title: str, uuid: str):
    prompt = prompts.IMAGE_DESCRIPTION.replace(r"{title}", title)
    completion, usage = llm_completion(prompt, 50)
    image_description = extract_text_from_quotes(completion)
    image_url = generate_image(image_description)
    save_file_path = f"{settings.IMAGE_PATH}/{uuid}.png"
    success = save_image_from_url(image_url, save_file_path)
    return success, image_description
