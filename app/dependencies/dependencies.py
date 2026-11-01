from database import sessionmanager
from flask import g
from protocols.service import EventService
from protocols.storage import Storage
from repository.sqlite_repo import SqliteStorage
from services.event_service import CustomEventService
from sqlalchemy.orm import Session


def get_db_session() -> Session:
    """Returns the request-scoped database session, opening it on first access"""
    if "db_session" not in g:
        g.db_session = sessionmanager.sessionmaker()

    return g.db_session


def close_db_session(exception=None) -> None:
    """Closes the request-scoped database session"""
    session = g.pop("db_session", None)

    if session is None:
        return

    if exception is not None:
        session.rollback()

    session.close()


def get_event_service() -> EventService:
    """Returns an event service wired with the SQLite storage"""
    storage: Storage = SqliteStorage(get_db_session())

    return CustomEventService(storage)
