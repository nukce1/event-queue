from pydantic import computed_field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    database_path: str = "./events.db"

    worker_enabled: bool = True
    worker_poll_interval: float = 1.0
    retry_base_delay: float = 1.0
    retry_backoff_factor: float = 2.0

    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    log_path: str = ""

    @computed_field
    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.database_path}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
