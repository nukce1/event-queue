from http import HTTPStatus


def post_event(client, event_id: str, event_type: str, payload: dict) -> None:
    response = client.post("/webhook", json={"event_id": event_id, "type": event_type, "payload": payload})

    assert response.status_code == HTTPStatus.OK


def test_stats_empty_on_fresh_database(client):
    response = client.get("/stats")

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {
        "events_by_type": {},
        "tasks_by_status": {"pending": 0, "success": 0, "failed": 0, "skipped": 0},
    }


def test_stats_count_events_by_type_and_tasks_by_status(client, drain):
    post_event(client, "fail-1", "payment_succeeded", {"simulate_failure": True})
    post_event(client, "ok-1", "payment_succeeded", {"amount": 100})
    post_event(client, "refund-1", "refund_issued", {"amount": 50})

    drain()

    response = client.get("/stats")

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {
        "events_by_type": {"payment_succeeded": 2, "refund_issued": 1},
        "tasks_by_status": {"pending": 0, "success": 2, "failed": 1, "skipped": 0},
    }
