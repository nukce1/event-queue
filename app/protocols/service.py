from typing import Protocol

from domain.schemas import (
    StatsRead,
    WebhookAcceptRead,
    WebhookCreate,
)


class EventService(Protocol):
    def create_event(self, webhook: WebhookCreate) -> WebhookAcceptRead: ...

    def get_stats(self) -> StatsRead: ...
