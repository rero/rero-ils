# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test for missing invenio_celery task endpoints."""

from importlib_metadata import entry_points
from invenio_records_rest.utils import obj_or_import_string


def test_missing_invenio_celery_task_endpoints(app):
    """Test missing invenio_celery task endpoints."""
    celery_extension = app.extensions["invenio-celery"]
    celery_entpoints = [e.value for e in entry_points(group=celery_extension.entry_point_group)]

    for data in app.config["CELERY_BEAT_SCHEDULE"].values():
        task_function = data["task"]
        # test if function exist
        assert obj_or_import_string(task_function)
        endpoint = ".".join(task_function.split(".")[:-1])
        # test if endpoint is defined in setup.py in invenio_celery.tasks
        assert endpoint in celery_entpoints
