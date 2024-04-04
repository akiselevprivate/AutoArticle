from settings.settings import settings
from utils.other import extract_json
from settings.logger import logger

# from openlimit import ChatRateLimiter  # https://github.com/shobrook/openlimit
from openai import OpenAI, RateLimitError
from typing import Callable

from utils.rate_limmiter import RateLimiter

MODEL = "gpt-3.5-turbo-1106"


openai_client = OpenAI(api_key=settings.OPENAI_KEY)
rate_limiter = RateLimiter()


@rate_limiter.request
def llm_completion(
    prompt: str,
    max_tokens: int,
    return_json: bool = False,
    model: str = None,
    temperature: float = 1,
    top_p: float = 1,
    frequency_penalty: float = 0,
    presence_penalty: float = 0,
):
    chat_params = dict(
        model=model if model else MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )

    if return_json:
        chat_params["response_format"] = {"type": "json_object"}

    response = openai_client.chat.completions.create(**chat_params)
    return (
        response.choices[0].message.content,
        response.usage,
    )


def json_llm_completion(
    prompt: str,
    max_tokens: int,
    model: str = None,
    throw_exception: bool = False,
    other_checks_func: Callable = None,
    temperature: float = 1,
    top_p: float = 1,
    frequency_penalty: float = 0,
    presence_penalty: float = 0,
):
    tries_count = 0
    all_usages = []
    while True:
        tries_count += 1
        logger.debug(f"Completion try: {tries_count}")
        completion, usage = llm_completion(
            prompt,
            max_tokens,
            return_json=True,
            model=model,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )
        all_usages.append(usage)
        try:
            dict_completion = extract_json(completion)
            if other_checks_func != None:
                assert other_checks_func(dict_completion)
            return dict_completion, all_usages
        except Exception as e:
            logger.error(e)
            logger.error("failed json completion input: " + str(completion))
            if tries_count == settings.INVALID_JSON_TRIES:
                if throw_exception:
                    raise Exception("failed json completion")
                return None, all_usages
