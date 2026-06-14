from pydantic_settings import BaseSettings
from langchain_openai import ChatOpenAI
from functools import lru_cache


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    alpha_vantage_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    bvl_data_dir: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_llm() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.deepseek_model,
        api_key=s.deepseek_api_key,
        base_url="https://api.deepseek.com",
        temperature=0.1,
        max_tokens=2048,
    )
