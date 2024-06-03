# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Common pytest fixtures and plugins."""

from datetime import timedelta
from os.path import dirname, join

import pytest


@pytest.fixture(scope="module")
def create_app():
    """Create test app."""
    from invenio_app.factory import create_api

    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Create temporary instance dir for each test."""
    app_config["CELERY_BROKER_URL"] = "memory://"
    app_config["RATELIMIT_STORAGE_URL"] = "memory://"
    app_config["CACHE_TYPE"] = "simple"
    app_config["SEARCH_ELASTIC_HOSTS"] = None
    app_config["DB_VERSIONING"] = True
    app_config["CELERY_CACHE_BACKEND"] = "memory"
    app_config["CELERY_RESULT_BACKEND"] = "cache"
    app_config["CELERY_TASK_ALWAYS_EAGER"] = True
    app_config["CELERY_TASK_EAGER_PROPAGATES"] = True
    app_config["CELERY_BEAT_SCHEDULER"] = "rero_ils.schedulers.RedisScheduler"
    app_config["CELERY_REDIS_SCHEDULER_URL"] = "redis://localhost:6379/4"
    app_config["CELERY_BEAT_SCHEDULE"] = {
        "bulk-indexer": {
            "task": "rero_ils.modules.tasks.process_bulk_queue",
            "schedule": timedelta(minutes=60),
            "enabled": False,
        }
    }
    help_test_dir = join(dirname(__file__), "data", "help")
    app_config["WIKI_CONTENT_DIR"] = help_test_dir
    app_config["WIKI_UPLOAD_FOLDER"] = join(help_test_dir, "files")
    return app_config
