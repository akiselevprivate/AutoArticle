from dotenv import load_dotenv
from dataclasses import dataclass, asdict, fields, _MISSING_TYPE
import os


@dataclass
class Settings:

    OPENAI_KEY: str

    WP_USER: str
    WP_APPLICATION_PASSWORD: str
    SITE_URL: str

    SQLITE_DB_FILE: str

    TOPIC: str
    GEN_TITLES_COUNT: int
    ARTICLE_SECTIONS_COUNT: int
    ARTICLE_LINK_COUNT: int

    CATEGORIES_COUNT: int

    REMOVE_FIRST_H3: bool

    PUBLISH_STATUS: str

    IMAGE_PATH: str
    GENERATE_IMAGE: bool

    EXTRA_IMAGES_PER_ARTICLE: int

    REPLICATE_API_TOKEN: str
    IMAGE_MODEL: str
    IMAGE_HEIGHT: int
    IMAGE_WIDTH: int
    UPSCALE_STEPS: int
    IMAGE_NEGATIVE_PROMPT: str
    IMAGE_INFERENCE_STEPS: int

    EMBEDDINGS_DB_PATH: str
    EMBEDDINGS_OPENAI_MODEL: str

    PERPLEXITY_API_KEY: str

    SUFFIX_URL: str = ""

    OPENAI_MINUTE_RATE_LIMIT: int = 3500
    OPENAI_MINUTE_TOKEN_RATE_LIMIT: int = 60000

    PRICE_PER_THOUSAND_INPUT_TOKENS: float = 0.001
    PRICE_PER_THOUSAND_OUTPUT_TOKENS: float = 0.002

    OUTLINE_PROMPT_FILE: str = "prompts/outline.txt"
    SECTION_PROMPT_FILE: str = "prompts/sections.txt"
    TITLE_PROMPT_FILE: str = "prompts/titles.txt"
    CATEGORIES_PROMPT_FILE: str = "prompts/categories.txt"
    ANCHORS_PROMPT_FILE: str = "prompts/anchors.txt"
    ADDITIONAL_DATA_PROMPT_FILE: str = "prompts/additional_data.txt"
    IMAGE_GENERATION_PROMPT_FILE: str = "prompts/image_generation.txt"
    IMAGE_DESCRIPTION_PROMPT_FILE: str = "prompts/image_description.txt"
    DATA_SPLIT_PROMPT_FILE: str = "prompts/data_split.txt"

    INVALID_JSON_TRIES: int = 3
    MAX_SECTION_RETRIES: int = 3
    MAX_ANCHOR_RETRIES: int = 2

    def model_dump(self):
        return asdict(self)

    @classmethod
    def from_env_file(cls, file_path=".env"):
        load_dotenv(file_path, override=True)
        env_vars = dict(os.environ)

        # Convert values to the specified types
        converted_vars = {}
        for field in fields(cls):
            field_name = field.name
            field_type = field.type
            if type(field.default) != _MISSING_TYPE:
                converted_vars[field_name] = field.default
                continue
            if field_name in env_vars and env_vars[field_name] is not None:
                if field_type == bool:
                    converted_vars[field_name] = env_vars[field_name].lower() == "true"
                else:
                    converted_vars[field_name] = field_type(env_vars[field_name])
        return cls(**converted_vars)


# Create Settings instance
settings = Settings.from_env_file()
# print(settings.model_dump())
