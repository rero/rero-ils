# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Celery application for Invenio flavours."""

from dotenv import load_dotenv
from flask_celeryext import create_celery_app
from invenio_app.factory import create_ui

# load .env and .flaskenv
load_dotenv()

celery = create_celery_app(
    create_ui(
        SENTRY_TRANSPORT="raven.transport.http.HTTPTransport",
        RATELIMIT_ENABLED=False,
    )
)
"""Celery application for Invenio.
Overrides SENTRY_TRANSPORT wih synchronous HTTP transport since Celery does not
deal nicely with the default threaded transport.
"""

# Trigger an app log message upon import. This makes Sentry logging
# work with `get_task_logger(__name__)`.
celery.flask_app.logger.info("Created Celery app")
