from settings.settings import settings
from utils.other import extract_json
from settings.logger import logger

# from openlimit import ChatRateLimiter  # https://github.com/shobrook/openlimit
from openai import OpenAI, RateLimitError
from typing import Callable

from utils.rate_limmiter import RateLimiter

MODEL = "gpt-3.5-turbo"


openai_client = OpenAI(api_key=settings.OPENAI_KEY)
rate_limiter = RateLimiter()


@rate_limiter.request
def llm_completion(prompt: str, max_tokens: int):
    chat_params = dict(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=max_tokens,
    )

    response = openai_client.chat.completions.create(**chat_params)
    return (
        response.choices[0].message.content,
        response.usage,
    )


def json_llm_completion(
    prompt: str,
    max_tokens: int,
    throw_exception: bool = False,
    other_checks_func: Callable = None,
):
    tries_count = 0
    all_usages = []
    while True:
        tries_count += 1
        logger.debug(f"Completion try: {tries_count}")
        completion, usage = llm_completion(prompt, max_tokens)
        all_usages.append(usage)
        try:
            dict_completion = extract_json(completion)
            if other_checks_func:
                assert other_checks_func(dict_completion)
            return dict_completion, all_usages
        except Exception as e:
            logger.error(e)
            logger.error("failed json completion input: " + str(completion))
            if tries_count == settings.INVALID_JSON_TRIES:
                if throw_exception:
                    raise Exception("failed json completion")
                return None, all_usages
