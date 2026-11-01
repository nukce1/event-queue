import logging

from domain.schemas import (
    StatsRead,
    WebhookAcceptRead,
    WebhookCreate,
)
from protocols.storage import Storage
from services.exceptions import StorageInternalException


class CustomEventService:
    def __init__(self, storage: Storage):
        self.storage = storage

    def create_event(self, webhook: WebhookCreate) -> WebhookAcceptRead:
        """
        Saves a webhook event and enqueues a processing task for it
        Args:
            webhook: Validated webhook body

        Returns:
            WebhookAcceptRead: Acceptance result ("accepted" or "duplicate")
        """
        try:
            created = self.storage.create_event_with_task(webhook)

        except Exception as exc:
            logging.error(f"Error while saving event {webhook.event_id} to storage - {exc}")
            raise StorageInternalException(message="Error while saving event to storage")

        if not created:
            return WebhookAcceptRead(result="duplicate")

        return WebhookAcceptRead(result="accepted")

    def get_stats(self) -> StatsRead:
        """
        Returns event counters by type and task counters by status
        Returns:
            StatsRead: Counters for events and tasks
        """
        try:
            events_by_type = self.storage.count_events_by_type()
            tasks_by_status = self.storage.count_tasks_by_status()

        except Exception as exc:
            logging.error(f"Error while getting stats from storage - {exc}")
            raise StorageInternalException(message="Error while getting stats from storage")

        return StatsRead(events_by_type=events_by_type, tasks_by_status=tasks_by_status)
