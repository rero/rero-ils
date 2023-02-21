# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Celery application for Invenio flavours."""

from __future__ import absolute_import, print_function

from dotenv import load_dotenv
from flask_celeryext import create_celery_app
from invenio_app.factory import create_ui

# load .env and .flaskenv
load_dotenv()

celery = create_celery_app(create_ui(
    SENTRY_TRANSPORT='raven.transport.http.HTTPTransport',
    RATELIMIT_ENABLED=False,
))
"""Celery application for Invenio.
Overrides SENTRY_TRANSPORT wih synchronous HTTP transport since Celery does not
deal nicely with the default threaded transport.
"""

# Trigger an app log message upon import. This makes Sentry logging
# work with `get_task_logger(__name__)`.
celery.flask_app.logger.info('Created Celery app')
