import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError


with patch.dict(os.environ, {
    "DATABASE_URL": "postgresql://test:test@localhost:5433/test",
    "REDIS_URL": "redis://localhost:6379/0",
    "OPENAI_API_KEY": "test-key",
}):
    import worker


class WorkerQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        cleanup = patch("worker.remove_expired_job_directories", return_value=[])
        cleanup.start()
        self.addCleanup(cleanup.stop)
        storage = patch("worker.r2_storage", None)
        storage.start()
        self.addCleanup(storage.stop)

    def test_recovers_after_connection_and_timeout_errors(self) -> None:
        for error_type in (RedisConnectionError, RedisTimeoutError):
            for queue in (b"jobs", b"clip_adjustments"):
                with self.subTest(error=error_type.__name__, queue=queue):
                    output = io.StringIO()
                    with (
                        patch("worker.redis_client") as redis,
                        patch("worker.sleep") as sleep,
                        patch("worker.process_job") as process_job,
                        patch("worker.process_clip_adjustment") as process_adjustment,
                        redirect_stdout(output),
                    ):
                        redis.blpop.side_effect = [
                            error_type("secret-like-error-message"),
                            (queue, b"test-payload"),
                            KeyboardInterrupt(),
                        ]
                        with self.assertRaises(KeyboardInterrupt):
                            worker.run_worker()

                        sleep.assert_called_once_with(5)
                        self.assertEqual(redis.blpop.call_count, 3)
                        if queue == b"jobs":
                            process_job.assert_called_once_with("test-payload")
                            process_adjustment.assert_not_called()
                        else:
                            process_adjustment.assert_called_once_with(b"test-payload")
                            process_job.assert_not_called()
                        self.assertIn(error_type.__name__, output.getvalue())
                        self.assertNotIn("secret-like-error-message", output.getvalue())

    def test_empty_queue_continues_without_retry_delay(self) -> None:
        with (
            patch("worker.redis_client") as redis,
            patch("worker.sleep") as sleep,
            patch("worker.process_job") as process_job,
            patch("worker.process_clip_adjustment") as process_adjustment,
        ):
            redis.blpop.side_effect = [None, KeyboardInterrupt()]
            with self.assertRaises(KeyboardInterrupt):
                worker.run_worker()
            self.assertEqual(redis.blpop.call_count, 2)
            sleep.assert_not_called()
            process_job.assert_not_called()
            process_adjustment.assert_not_called()

    def test_unexpected_error_is_not_hidden(self) -> None:
        with patch("worker.redis_client") as redis, patch("worker.sleep") as sleep:
            redis.blpop.side_effect = ValueError("unexpected")
            with self.assertRaises(ValueError):
                worker.run_worker()
            sleep.assert_not_called()

    def test_keyboard_interrupt_still_stops_worker(self) -> None:
        with patch("worker.redis_client") as redis, patch("worker.sleep") as sleep:
            redis.blpop.side_effect = KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                worker.run_worker()
            sleep.assert_not_called()
