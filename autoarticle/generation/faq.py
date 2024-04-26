from settings import prompts
from utils.llm import json_llm_completion


def generate_faq(data: str, topic: str, title: str, ammount: str):

    if data:
        base_prompt = prompts.FAQ.replace(r"{data_split}", "").replace(r"{data}", data)
    else:
        base_prompt = prompts.FAQ.split(r"{data_split}")[1]

    prompt = (
        base_prompt.replace(r"{ammount}", str(ammount))
        .replace(r"{topic}", topic)
        .replace(r"{title}", title)
    )

    def test_dict_output(dict_completion):
        return (
            "faq" in dict_completion.keys() and len(dict_completion["faq"]) >= ammount
        )

    faq_dict, all_usages = json_llm_completion(
        prompt,
        800,
        throw_exception=True,
        other_checks_func=test_dict_output,
    )

    return faq_dict["faq"]
