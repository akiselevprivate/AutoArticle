from openai import AsyncOpenAI
from settings.settings import settings
from utils.other import extract_json
from settings.logger import logger
import asyncio

client = AsyncOpenAI(api_key=settings.OPENAI_KEY)

global_input_token_usage = 0
global_output_token_usage = 0


def llm_completion(prompts, max_tokens):
    global global_input_token_usage
    global global_output_token_usage

    async def llm_completion_async(prompt, prompt_index, max_tokens):
        global global_input_token_usage
        global global_output_token_usage
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=max_tokens,
        )

        global_input_token_usage += response.usage.prompt_tokens
        global_output_token_usage += response.usage.completion_tokens

        return (
            prompt_index,
            response.choices[0].message.content,
            response.usage.total_tokens,
        )

    async def main():
        tasks = [
            llm_completion_async(prompt, index, max_tokens)
            for index, prompt in enumerate(prompts)
        ]
        results = await asyncio.gather(*tasks)
        results.sort(key=lambda x: x[0])
        completions, total_usage = zip(*[(result[1], result[2]) for result in results])
        return completions, sum(total_usage)

    return asyncio.run(main())


# def llm_completion(prompts: list, max_tokens: int):
#     global global_input_token_usage
#     global global_output_token_usage
#     completions = []
#     total_usage = 0
#     for p in prompts:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo-1106",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": p,
#                 }
#             ],
#             max_tokens=max_tokens,
#         )
#         total_usage += response.usage.total_tokens
#         response.
#         global_input_token_usage += response.usage.prompt_tokens
#         global_output_token_usage += response.usage.completion_tokens
#         completions.append(response.choices[0].message.content)

#     # completions = [None] * len(prompts)
#     # for choice in response.choices:
#     #     completions[choice.index] = choice.message.content

#     return completions, total_usage


def llm_json_completion(
    prompts: list,
    max_tokens: int,
    throw_exception: bool = False,
    other_checks_func=None,
):
    tries_count = 0
    completions_with_idx = []
    token_usage = 0
    successful_completions_count = 0
    not_prompts_with_idx = [[idx, prompt] for idx, prompt in enumerate(prompts)]
    while (
        tries_count <= settings.INVALID_JSON_TRIES
        and not successful_completions_count == len(prompts)
    ):
        run_completions_indexes = [idx for idx, _ in not_prompts_with_idx]
        run_prompts = [prompt for _, prompt in not_prompts_with_idx]
        run_completions, run_token_usage = llm_completion(run_prompts, max_tokens)
        token_usage += run_token_usage

        not_prompts_with_idx = []
        for idx, completion, prompt in zip(
            run_completions_indexes, run_completions, run_prompts
        ):
            try:
                dict_completion = extract_json(completion)
                if other_checks_func:
                    assert other_checks_func(dict_completion)
                successful_completions_count += 1
                failed = False
            except Exception as e:
                logger.error(e)
                logger.error("failed completion input: " + str(completion))
                dict_completion = None
                failed = True
            if failed:
                if tries_count != settings.INVALID_JSON_TRIES:
                    not_prompts_with_idx.append([idx, prompt])
                else:
                    completions_with_idx.append([idx, dict_completion])  # None
            else:
                completions_with_idx.append([idx, dict_completion])
        tries_count += 1

    logger.info(f"Completion tries: {tries_count}")

    if throw_exception:
        assert successful_completions_count == len(prompts)

    completions_list = [None] * len(prompts)
    for idx, copmletion_dict in completions_with_idx:
        completions_list[idx] = copmletion_dict

    return completions_list, token_usage
