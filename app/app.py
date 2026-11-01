import logging

from api.v1.stats import stats_blueprint
from api.v1.webhooks import webhook_blueprint
from config import settings
from database import (
    Base,
    DatabaseSessionException,
    sessionmanager,
)
from dependencies.dependencies import close_db_session
from flask import Flask
from worker.worker import QueueWorker


def init_app() -> Flask:
    logging.basicConfig(
        level=settings.log_level,
        format=settings.log_format,
        datefmt=settings.log_date_format,
        filename=settings.log_path or None,
        filemode="a",
    )

    app = Flask(__name__)
    app.register_blueprint(webhook_blueprint)
    app.register_blueprint(stats_blueprint)
    app.teardown_appcontext(close_db_session)

    sessionmanager.init(settings.sqlite_url)

    if sessionmanager.engine is None:
        logging.error("DatabaseSessionManager is not initialized")
        raise DatabaseSessionException()

    Base.metadata.create_all(sessionmanager.engine)
    logging.info("Database connection established.")

    if settings.worker_enabled:
        QueueWorker(session_factory=sessionmanager.session).start()

    return app


app = init_app()
