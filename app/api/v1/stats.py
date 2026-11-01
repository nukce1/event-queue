from http import HTTPStatus

from dependencies.dependencies import get_event_service
from flask import (
    Blueprint,
    jsonify,
)
from protocols.service import EventService
from services.exceptions import StorageInternalException

stats_blueprint = Blueprint("stats", __name__)


@stats_blueprint.get("/stats")
def get_stats_handler():
    """Returns event counters by type and task counters by status"""
    try:
        event_service: EventService = get_event_service()
        stats = event_service.get_stats()

    except StorageInternalException as exc:
        return jsonify(detail=str(exc)), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as exc:
        return jsonify(detail=str(exc)), HTTPStatus.BAD_REQUEST

    return jsonify(stats.model_dump()), HTTPStatus.OK
