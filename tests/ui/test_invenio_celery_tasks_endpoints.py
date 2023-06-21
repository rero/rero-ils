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

"""Test for missing invenio_celery task endpoints."""

from __future__ import absolute_import, print_function

from importlib_metadata import entry_points
from invenio_records_rest.utils import obj_or_import_string


def test_missing_invenio_celery_task_endpoints(app):
    """Test missing invenio_celery task endpoints."""
    celery_extension = app.extensions['invenio-celery']
    celery_entpoints = [
        e.value
        for e in entry_points(group=celery_extension.entry_point_group)
    ]

    for task, data in app.config['CELERY_BEAT_SCHEDULE'].items():
        task_function = data['task']
        # test if function exist
        assert obj_or_import_string(task_function)
        endpoint = '.'.join(task_function.split('.')[:-1])
        # test if endpoint is defined in setup.py in invenio_celery.tasks
        assert endpoint in celery_entpoints
