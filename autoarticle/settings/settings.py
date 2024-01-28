from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env")

    OPENAI_KEY: str
    LINKING_URL_PATH: str

    SQLITE_DB_FILE: str

    OUTLINE_PROMPT_FILE: str
    SECTION_PROMPT_FILE: str
    TITLE_PROMPT_FILE: str
    ALTERNATIVE_TITLE_PROMPT_FILE: str

    ARTICLES_PATH: str

    # Article generation

    ARTICLE_TYPE: str
    TOPIC: str
    GEN_TITLES_COUNT: int
    GEN_ARTICLES_COUNT: int
    JSON_TITLE_EXAMPLES_FILE: str
    ARTICLE_SECTIONS_COUNT: int
    LINKING_TITLES_IN_SECTION_COUNT: int

    INVALID_JSON_TRIES: int
    EXISTING_TITLES: bool


settings = Settings()
