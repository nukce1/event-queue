import logging
import threading
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import timedelta

from config import settings
from domain.models import utcnow
from domain.schemas import TaskRead
from protocols.storage import Storage
from repository.constants import MAX_TASK_ATTEMPTS
from repository.sqlite_repo import SqliteStorage
from sqlalchemy.orm import Session
from worker.handlers import EVENT_HANDLERS


class QueueWorker:
    """Processes due queue tasks in a background thread"""

    def __init__(self, session_factory: Callable[[], AbstractContextManager[Session]]):
        self.session_factory = session_factory
        self.handlers = EVENT_HANDLERS
        self.poll_interval = settings.worker_poll_interval
        self._stop_event = threading.Event()

    def process_next_task(self) -> bool:
        """
        Claims one due task, dispatches it to its handler and records the result
        Returns:
            bool: True if a task was claimed, False when no due task was found
        """
        with self.session_factory() as session:
            storage: Storage = SqliteStorage(session)
            task = storage.claim_next_due_task(now=utcnow())

            if task is None:
                return False

            self._dispatch(storage, task)

        return True

    def _dispatch(self, storage: Storage, task: TaskRead) -> None:
        event = storage.get_event_by_pk(task.event_id)

        if event is None:
            storage.set_task_failed(task.id, error="Linked event is missing")
            return

        handler = self.handlers.get(event.type)

        if handler is None:
            logging.info(f"Task {task.id} skipped: no handler for event type '{event.type}'")
            storage.set_task_skipped(task.id, reason=f"No handler for event type '{event.type}'")
            return

        try:
            handler(event.payload)

        except Exception as exc:
            logging.error(f"Task {task.id} failed on attempt {task.attempts} - {exc}")
            self._record_failure(storage, task, error=str(exc))

        else:
            logging.info(f"Task {task.id} processed successfully")
            storage.set_task_success(task.id)

    def _record_failure(self, storage: Storage, task: TaskRead, error: str) -> None:
        """Retries the task with a growing delay or marks it permanently failed after the attempt limit"""
        if task.attempts >= MAX_TASK_ATTEMPTS:
            storage.set_task_failed(task.id, error=error)
            return

        delay = settings.retry_base_delay * settings.retry_backoff_factor ** (task.attempts - 1)
        storage.set_task_retry(task.id, next_run_at=utcnow() + timedelta(seconds=delay), error=error)

    def run(self) -> None:
        logging.info("Queue worker started.")

        while not self._stop_event.is_set():
            processed = self.process_next_task()

            if not processed:
                self._stop_event.wait(self.poll_interval)

        logging.info("Queue worker stopped.")

    def start(self) -> None:
        threading.Thread(target=self.run, name="queue-worker", daemon=True).start()

    def stop(self) -> None:
        self._stop_event.set()
