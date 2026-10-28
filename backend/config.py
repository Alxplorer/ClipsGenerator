from ipaddress import ip_address
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_local_hostname(hostname: str | None) -> bool:
    if hostname is None:
        return True
    normalized = hostname.rstrip(".").lower()
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        address = ip_address(normalized)
    except ValueError:
        return False
    return address.is_loopback or address.is_unspecified


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    openai_api_key: SecretStr | None = None
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    frontend_origin: str = "http://localhost:3000"
    render: bool = False
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
    def worker_openai_api_key(self) -> str:
        if self.openai_api_key is None:
            raise ValueError("El worker necesita OPENAI_API_KEY.")
        return self.openai_api_key.get_secret_value()

    def check_deployment(self, service: Literal["api", "worker"]) -> None:
        if not self.render:
            return

        for name, address in (
            ("DATABASE_URL", self.database_url),
            ("REDIS_URL", self.redis_url),
        ):
            hostname = urlsplit(address).hostname
            if is_local_hostname(hostname):
                raise ValueError(f"{name} debe apuntar a un servicio remoto en Render.")

        if not self.r2_configured:
            raise ValueError("API y worker necesitan las cuatro variables R2 en Render.")

        if service == "api":
            origin = urlsplit(self.frontend_origin)
            if (
                origin.scheme != "https"
                or is_local_hostname(origin.hostname)
                or origin.username is not None
                or origin.password is not None
                or self.frontend_origin != f"{origin.scheme}://{origin.netloc}"
            ):
                raise ValueError("FRONTEND_ORIGIN debe ser el origen HTTPS público de la web.")
        else:
            _ = self.worker_openai_api_key

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
