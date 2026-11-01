import os
import tempfile


def configure_test_environment() -> None:
    """Points the app settings at an isolated test database before the app modules are imported"""
    test_dir = tempfile.mkdtemp(prefix="event-queue-tests-")

    os.environ.setdefault("DATABASE_PATH", os.path.join(test_dir, "tests.db"))
    os.environ.setdefault("LOG_PATH", os.path.join(test_dir, "app.log"))
    os.environ.setdefault("WORKER_ENABLED", "false")
    os.environ.setdefault("RETRY_BASE_DELAY", "0")
    os.environ.setdefault("LOG_LEVEL", "CRITICAL")


configure_test_environment()
