from datetime import datetime

from domain.models import (
    Event,
    Task,
    utcnow,
)
from domain.schemas import (
    EventRead,
    TaskRead,
    WebhookCreate,
)
from repository.constants import (
    TASK_STATUS_FAILED,
    TASK_STATUS_PENDING,
    TASK_STATUS_SKIPPED,
    TASK_STATUS_SUCCESS,
    TASK_STATUSES,
)
from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session


class SqliteStorage:
    def __init__(self, session: Session):
        self.session = session

    def create_event_with_task(self, webhook: WebhookCreate) -> bool:
        """
        Saves an event together with its pending task in one transaction
        Args:
            webhook: Validated webhook body

        Returns:
            bool: True if a new event was created, False if the event_id already existed
        """
        statement = (
            sqlite_insert(Event)
            .values(
                event_id=webhook.event_id,
                type=webhook.type,
                payload=webhook.payload,
            )
            .on_conflict_do_nothing(index_elements=["event_id"])
        )

        result = self.session.execute(statement)

        if result.rowcount == 0:
            return False

        task = Task(
            event_id=result.inserted_primary_key[0],
            status=TASK_STATUS_PENDING,
            next_run_at=utcnow(),
        )
        self.session.add(task)
        self.session.commit()

        return True

    def get_event_by_pk(self, event_pk: int) -> EventRead | None:
        """
        Returns an event by primary key
        Args:
            event_pk: Event primary key

        Returns:
            EventRead: Event or None when not found
        """
        query = select(Event).where(Event.id == event_pk)

        event_orm = self.session.execute(query).scalars().first()

        if event_orm is None:
            return None

        return EventRead.model_validate(event_orm)

    def claim_next_due_task(self, now: datetime) -> TaskRead | None:
        """
        Claims the earliest due pending task and burns one processing attempt
        Args:
            now: Current UTC timestamp

        Returns:
            TaskRead: Claimed task or None when the queue has no due tasks
        """
        query = (
            select(Task)
            .where(Task.status == TASK_STATUS_PENDING, Task.next_run_at <= now)
            .order_by(Task.next_run_at, Task.id)
            .limit(1)
        )

        task_orm = self.session.execute(query).scalars().first()

        if task_orm is None:
            return None

        task_orm.attempts += 1
        task_orm.next_run_at = now
        task_orm.updated_at = now
        self.session.commit()

        return TaskRead.model_validate(task_orm)

    def set_task_success(self, task_id: int) -> None:
        """Marks the task as successfully processed"""
        statement = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=TASK_STATUS_SUCCESS, last_error=None, updated_at=utcnow())
        )
        self.session.execute(statement)
        self.session.commit()

    def set_task_retry(self, task_id: int, next_run_at: datetime, error: str) -> None:
        """Returns the task to the pending queue with a new run time"""
        statement = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=TASK_STATUS_PENDING, next_run_at=next_run_at, last_error=error, updated_at=utcnow())
        )
        self.session.execute(statement)
        self.session.commit()

    def set_task_failed(self, task_id: int, error: str) -> None:
        """Marks the task as permanently failed"""
        statement = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=TASK_STATUS_FAILED, last_error=error, updated_at=utcnow())
        )
        self.session.execute(statement)
        self.session.commit()

    def set_task_skipped(self, task_id: int, reason: str) -> None:
        """Marks the task as skipped"""
        statement = (
            update(Task)
            .where(Task.id == task_id)
            .values(status=TASK_STATUS_SKIPPED, last_error=reason, updated_at=utcnow())
        )
        self.session.execute(statement)
        self.session.commit()

    def count_events_by_type(self) -> dict[str, int]:
        """
        Returns event counters grouped by event type
        Returns:
            dict[str, int]: Event type to event count
        """
        query = select(Event.type, func.count()).group_by(Event.type)

        rows = self.session.execute(query).all()

        return dict(rows)

    def count_tasks_by_status(self) -> dict[str, int]:
        """
        Returns task counters grouped by status, zero statuses included
        Returns:
            dict[str, int]: Task status to task count
        """
        query = select(Task.status, func.count()).group_by(Task.status)

        rows = self.session.execute(query).all()
        counts = dict.fromkeys(TASK_STATUSES, 0)
        counts.update(dict(rows))

        return counts
