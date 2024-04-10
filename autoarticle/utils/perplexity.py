from openai import OpenAI
from settings.settings import settings


client = OpenAI(
    api_key=settings.PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai"
)


def perplexity_llm(prompt: str, max_tokens: int):
    response = client.chat.completions.create(
        model="sonar-medium-online",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=max_tokens,
    )

    return (response.choices[0].message.content, response.usage)
