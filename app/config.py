from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env.

    All values are placeholders until real credentials are supplied.
    No code changes should be needed to go live — only .env.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Azure's OpenAI-compatible v1 API — no api_version needed.
    azure_openai_endpoint: str = "https://PLACEHOLDER.services.ai.azure.com/openai/v1"
    azure_openai_api_key: str = "PLACEHOLDER-api-key"
    azure_openai_deployment: str = "PLACEHOLDER-deployment-name"

    # Exact frontend origins to allow, comma-separated. Empty until set.
    cors_allowed_origins: str = ""
    # Secure by default: localhost only. Scope this to your real domain via
    # env var (e.g. r"^https://my-project(-[a-z0-9-]+)?\.vercel\.app$")
    # rather than widening it — a blanket *.vercel.app wildcard here once
    # let any Vercel-hosted origin burn this app's LLM budget.
    cors_allowed_origin_regex: str = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"

    # Basic per-IP abuse protection for the public /chat endpoint.
    rate_limit_max_requests: int = 20
    rate_limit_window_seconds: float = 60.0


settings = Settings()
