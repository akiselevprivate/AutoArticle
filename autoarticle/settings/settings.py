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

    SQLITE_DB_FILE: str

    OUTLINE_PROMPT_FILE: str
    SECTION_PROMPT_FILE: str
    TITLE_PROMPT_FILE: str

    ARTICLES_PATH: str

    # Article generation

    ADDITIONAL_TITLE_SETTINGS: str

    ARTICLE_TYPE: str
    TOPIC: str
    GEN_TITLES_COUNT: int
    GEN_ARTICLES_COUNT: int
    JSON_TITLE_EXAMPLES_FILE: str
    JSON_FAQ_EXAMPLES_FILE: str
    CATEGORIES_COUNT: int
    FAQ_AMMOUNT: int
    ARTICLE_SECTIONS_COUNT: int
    LINKING_TITLES_IN_SECTION_COUNT: int

    INVALID_JSON_TRIES: int
    EXISTING_TITLES: bool

    REMOVE_TOP_H2: bool

    UPLOAD_WITH_FAQ: bool
    UPLOAD_WITH_TITLE: bool
    PUBLISH_STATUS: str

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
