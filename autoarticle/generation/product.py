from settings import prompts
from utils.llm import json_llm_completion


def generate_product_outline(
    description: str, reviews: list[str], full_name: str, price: float
):

    prompt = (
        prompts.PRODUCT_OUTLINE.replace(r"{description}", description)
        .replace(r"{reviews}", "\n".join(reviews))
        .replace(r"{name}", full_name)
        .replace(r"{price}", f"${price}")
    )

    def test_dict_output(dict_completion):
        return all(
            [
                v in dict_completion.keys()
                for v in ["pros", "cons", "short_name", "summary"]
            ]
        )

    product_outline, all_usages = json_llm_completion(
        prompt,
        800,
        throw_exception=True,
        other_checks_func=test_dict_output,
    )

    return product_outline
