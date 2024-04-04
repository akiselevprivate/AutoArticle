from dotenv import load_dotenv
from dataclasses import dataclass, asdict, fields
import os


@dataclass
class Settings:
    # model_config = SettingsConfigDict(case_sensitive=False, env_file=".env")

    OPENAI_KEY: str
    OPENAI_MINUTE_RATE_LIMIT: int
    OPENAI_MINUTE_TOKEN_RATE_LIMIT: int

    PRICE_PER_THOUSAND_INPUT_TOKENS: float
    PRICE_PER_THOUSAND_OUTPUT_TOKENS: float

    WP_USER: str
    WP_APPLICATION_PASSWORD: str
    SITE_URL: str
    SUFFIX_URL: str

    SQLITE_DB_FILE: str

    OUTLINE_PROMPT_FILE: str
    SECTION_PROMPT_FILE: str
    TITLE_PROMPT_FILE: str
    CATEGORIES_PROMPT_FILE: str
    ANCHORS_PROMPT_FILE: str

    # Article generation

    TOPIC: str
    GEN_TITLES_COUNT: int
    ARTICLE_SECTIONS_COUNT: int

    CATEGORIES_COUNT: int

    INVALID_JSON_TRIES: int
    MAX_SECTION_RETRIES: int

    PUBLISH_STATUS: str

    IMAGE_GENERATION_PROMPT_FILE: str
    IMAGE_DESCRIPTION_PROMPT_FILE: str
    IMAGE_PATH: str
    GENERATE_IMAGE: bool

    REPLICATE_API_TOKEN: str
    IMAGE_MODEL: str
    IMAGE_HEIGHT: int
    IMAGE_WIDTH: int
    UPSCALE_STEPS: int
    IMAGE_NEGATIVE_PROMPT: str
    IMAGE_INFERENCE_STEPS: int

    EMBEDDINGS_DB_PATH: str
    EMBEDDINGS_OPENAI_MODEL: str

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
            if field_name in env_vars and env_vars[field_name] is not None:
                if field_type == bool:
                    converted_vars[field_name] = env_vars[field_name].lower() == "true"
                else:
                    converted_vars[field_name] = field_type(env_vars[field_name])
        return cls(**converted_vars)


# Create Settings instance
settings = Settings.from_env_file()
# print(settings.model_dump())
