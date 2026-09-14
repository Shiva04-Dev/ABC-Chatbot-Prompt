from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env.

    All values are placeholders until Shiv supplies real ones (CLAUDE.md
    Section 10). No code changes should be needed to go live — only .env.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_endpoint: str = "https://PLACEHOLDER.openai.azure.com/"
    azure_openai_api_key: str = "PLACEHOLDER-api-key"
    azure_openai_deployment: str = "PLACEHOLDER-deployment-name"
    azure_openai_api_version: str = "PLACEHOLDER-api-version"


settings = Settings()
