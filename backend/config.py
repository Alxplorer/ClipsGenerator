from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    openai_api_key: SecretStr
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    r2_account_id: str | None = None
    r2_bucket_name: str | None = None
    r2_access_key_id: SecretStr | None = None
    r2_secret_access_key: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=Path(__file__).with_name(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        return self.database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    @property
    def r2_configured(self) -> bool:
        values = (
            self.r2_account_id,
            self.r2_bucket_name,
            self.r2_access_key_id.get_secret_value() if self.r2_access_key_id else None,
            self.r2_secret_access_key.get_secret_value() if self.r2_secret_access_key else None,
        )
        present = [bool(value) for value in values]
        if any(present) and not all(present):
            raise ValueError("Configura las cuatro variables R2 juntas.")
        return all(present)


settings = Settings()
