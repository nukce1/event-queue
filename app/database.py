import contextlib
import logging
from typing import (
    Annotated,
    Iterator,
)

from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    Session,
    declarative_base,
    mapped_column,
    sessionmaker,
)

Base = declarative_base()

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True, index=True)]


class DatabaseSessionManager:
    """Manages database sessions with a singleton pattern"""

    def __init__(self):
        self.engine: Engine | None = None
        self.sessionmaker: sessionmaker | None = None

    def init(self, dsn: str):
        self.engine = create_engine(dsn, connect_args={"timeout": 30})
        self.sessionmaker = sessionmaker(autocommit=False, bind=self.engine)

        event.listen(self.engine, "connect", set_sqlite_pragma)

    def close(self):
        if self.engine is None:
            logging.error("DatabaseSessionManager is not initialized")
            raise DatabaseSessionException()

        self.engine.dispose()
        self.engine = None
        self.sessionmaker = None

    @contextlib.contextmanager
    def session(self) -> Iterator[Session]:
        if self.sessionmaker is None:
            logging.error("DatabaseSessionManager is not initialized")
            raise DatabaseSessionException()

        session = self.sessionmaker()
        try:
            yield session

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()


def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enables WAL journaling and foreign key checks for every new SQLite connection"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


sessionmanager = DatabaseSessionManager()


class DatabaseSessionException(Exception):
    def __init__(self, message="DatabaseSessionManager is not initialized"):
        self.message = message
        super().__init__(self.message)
