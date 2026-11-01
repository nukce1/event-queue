import env  # noqa: F401
import pytest
from database import (
    Base,
    sessionmanager,
)
from worker.worker import QueueWorker

from app import init_app


@pytest.fixture()
def app():
    application = init_app()
    Base.metadata.drop_all(sessionmanager.engine)
    Base.metadata.create_all(sessionmanager.engine)
    yield application
    sessionmanager.close()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def worker():
    return QueueWorker(session_factory=sessionmanager.session)


@pytest.fixture()
def drain(worker):
    """Runs the worker until the queue has no due tasks left, returns the number of claimed tasks"""

    def _drain(max_tasks: int = 100) -> int:
        processed = 0

        while processed < max_tasks and worker.process_next_task():
            processed += 1

        return processed

    return _drain
