from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "model-serving-canary-platform"
    default_canary_percent: int = 25
    shadow_mode: bool = True
    baseline_model_name: str = "ticket-triage-v1"
    canary_model_name: str = "ticket-triage-v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
