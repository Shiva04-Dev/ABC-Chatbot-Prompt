from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env.

    All values are placeholders until Shiv supplies real ones (see Section 10
    of the project spec). No code changes should be needed to go live — only .env.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Azure's OpenAI-compatible v1 API — no api_version needed (confirmed
    # empirically against the real deployment; the v1 surface doesn't use
    # Azure OpenAI's older dated api_version scheme at all).
    azure_openai_endpoint: str = "https://PLACEHOLDER.services.ai.azure.com/openai/v1"
    azure_openai_api_key: str = "PLACEHOLDER-api-key"
    azure_openai_deployment: str = "PLACEHOLDER-deployment-name"

    # Comma-separated exact origins (e.g. the production frontend domain,
    # once it has one). Empty by default — nothing to allow until a
    # frontend exists.
    cors_allowed_origins: str = ""
    # Covers every Vercel deployment URL (production and preview builds
    # alike — M7's test UI) plus localhost, for testing the test UI itself
    # before it's ever deployed.
    cors_allowed_origin_regex: str = (
        r"^https://.*\.vercel\.app$|^http://(localhost|127\.0\.0\.1)(:\d+)?$"
    )

    # Basic per-IP abuse protection for the public /chat endpoint (Section 11 M6).
    rate_limit_max_requests: int = 20
    rate_limit_window_seconds: float = 60.0


settings = Settings()
