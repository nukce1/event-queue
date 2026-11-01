from http import HTTPStatus

from dependencies.dependencies import get_event_service
from domain.schemas import WebhookCreate
from flask import (
    Blueprint,
    jsonify,
    request,
)
from protocols.service import EventService
from pydantic import ValidationError
from services.exceptions import StorageInternalException

webhook_blueprint = Blueprint("webhooks", __name__)


@webhook_blueprint.post("/webhook")
def create_event_handler():
    """Accepts a webhook event and enqueues it for processing"""
    body = request.get_json(silent=True)

    if body is None:
        return jsonify(detail="Request body must be a JSON object."), HTTPStatus.BAD_REQUEST

    try:
        webhook = WebhookCreate.model_validate(body)

    except ValidationError as exc:
        errors = [
            {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]} for error in exc.errors()
        ]
        return jsonify(detail=errors), HTTPStatus.BAD_REQUEST

    try:
        event_service: EventService = get_event_service()
        result = event_service.create_event(webhook)

    except StorageInternalException as exc:
        return jsonify(detail=str(exc)), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as exc:
        return jsonify(detail=str(exc)), HTTPStatus.BAD_REQUEST

    return jsonify(result.model_dump()), HTTPStatus.OK
