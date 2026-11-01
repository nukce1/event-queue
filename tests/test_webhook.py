from http import HTTPStatus

import pytest

WEBHOOK_BODY = {
    "event_id": "abc-123",
    "type": "payment_succeeded",
    "payload": {"amount": 100},
}


def test_duplicate_webhook_does_not_create_second_event(client):
    """A repeated webhook with the same event_id must answer 200 and create no second record"""
    first_response = client.post("/webhook", json=WEBHOOK_BODY)
    second_response = client.post("/webhook", json=WEBHOOK_BODY)

    assert first_response.status_code == HTTPStatus.OK
    assert first_response.get_json() == {"result": "accepted"}

    assert second_response.status_code == HTTPStatus.OK
    assert second_response.get_json() == {"result": "duplicate"}

    stats = client.get("/stats").get_json()

    assert stats["events_by_type"] == {"payment_succeeded": 1}
    assert stats["tasks_by_status"]["pending"] == 1


def test_valid_event_is_stored_and_enqueued(client):
    response = client.post("/webhook", json=WEBHOOK_BODY)

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == {"result": "accepted"}

    stats = client.get("/stats").get_json()

    assert stats["events_by_type"] == {"payment_succeeded": 1}
    assert stats["tasks_by_status"]["pending"] == 1


@pytest.mark.parametrize(
    "body",
    [
        {"type": "payment_succeeded", "payload": {}},
        {"event_id": "", "type": "payment_succeeded", "payload": {}},
        {"event_id": "abc-123", "payload": {}},
        {"event_id": "abc-123", "type": "payment_succeeded"},
        {"event_id": "abc-123", "type": "payment_succeeded", "payload": "not-a-dict"},
        ["not", "an", "object"],
    ],
)
def test_invalid_body_returns_client_error(client, body):
    response = client.post("/webhook", json=body)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.get_json()["detail"]


def test_non_json_body_returns_client_error(client):
    response = client.post("/webhook", data="not-json", content_type="text/plain")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.get_json()["detail"] == "Request body must be a JSON object."
