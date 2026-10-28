import os
import unittest
from unittest.mock import patch


with patch.dict(os.environ, {
    "DATABASE_URL": "postgresql://test:test@localhost:5433/test",
    "REDIS_URL": "redis://localhost:6379/0",
}):
    from config import Settings


class OpenAIKeyConfigurationTests(unittest.TestCase):
    @staticmethod
    def render_settings(**overrides) -> Settings:
        values = {
            "render": True,
            "database_url": "postgresql://test:test@postgres.internal/test",
            "redis_url": "redis://redis.internal:6379/0",
            "frontend_origin": "https://clips.example.com",
            "r2_account_id": "example-account",
            "r2_bucket_name": "example-bucket",
            "r2_access_key_id": "example-id",
            "r2_secret_access_key": "example-secret",
            "openai_api_key": "example-key",
        }
        values.update(overrides)
        with patch.dict(os.environ, {}, clear=True):
            return Settings(_env_file=None, **values)

    def test_api_configuration_does_not_require_openai_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(
                _env_file=None,
                database_url="postgresql://test:test@localhost:5433/test",
                redis_url="redis://localhost:6379/0",
            )

        self.assertIsNone(settings.openai_api_key)
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            _ = settings.worker_openai_api_key

    def test_worker_reads_configured_openai_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(
                _env_file=None,
                database_url="postgresql://test:test@localhost:5433/test",
                redis_url="redis://localhost:6379/0",
                openai_api_key="example-key",
            )

        self.assertEqual(settings.worker_openai_api_key, "example-key")

    def test_render_accepts_remote_services(self) -> None:
        settings = self.render_settings()
        settings.check_deployment("api")
        settings.check_deployment("worker")

    def test_render_rejects_missing_r2_and_local_addresses(self) -> None:
        cases = (
            ({"r2_account_id": None, "r2_bucket_name": None,
              "r2_access_key_id": None, "r2_secret_access_key": None}, "R2"),
            ({"database_url": "postgresql://test:test@localhost/test"}, "DATABASE_URL"),
            ({"redis_url": "redis://127.0.0.1:6379/0"}, "REDIS_URL"),
            ({"frontend_origin": "http://localhost:3000"}, "FRONTEND_ORIGIN"),
        )
        for changes, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                with self.assertRaisesRegex(ValueError, expected_error):
                    self.render_settings(**changes).check_deployment("api")

    def test_render_worker_requires_openai_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            self.render_settings(openai_api_key=None).check_deployment("worker")
