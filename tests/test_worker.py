from http import HTTPStatus

from database import sessionmanager
from domain.models import Task
from sqlalchemy import select


def get_tasks() -> list[dict]:
    with sessionmanager.session() as session:
        tasks = session.execute(select(Task)).scalars().all()

        return [{"status": task.status, "attempts": task.attempts, "last_error": task.last_error} for task in tasks]


def test_task_processed_successfully(client, drain):
    body = {"event_id": "ok-1", "type": "payment_succeeded", "payload": {"amount": 100}}

    assert client.post("/webhook", json=body).status_code == HTTPStatus.OK

    assert drain() == 1

    tasks = get_tasks()

    assert len(tasks) == 1
    assert tasks[0]["status"] == "success"
    assert tasks[0]["attempts"] == 1
    assert tasks[0]["last_error"] is None


def test_task_fails_after_three_attempts_and_is_not_picked_again(client, drain):
    body = {"event_id": "fail-1", "type": "payment_succeeded", "payload": {"simulate_failure": True}}

    assert client.post("/webhook", json=body).status_code == HTTPStatus.OK

    assert drain() == 3

    tasks = get_tasks()

    assert len(tasks) == 1
    assert tasks[0]["status"] == "failed"
    assert tasks[0]["attempts"] == 3
    assert tasks[0]["last_error"] is not None

    assert drain() == 0


def test_unknown_event_type_is_skipped(client, drain):
    body = {"event_id": "strange-1", "type": "strange_event", "payload": {}}

    assert client.post("/webhook", json=body).status_code == HTTPStatus.OK

    assert drain() == 1

    tasks = get_tasks()

    assert len(tasks) == 1
    assert tasks[0]["status"] == "skipped"
    assert tasks[0]["attempts"] == 1
    assert "No handler" in tasks[0]["last_error"]
