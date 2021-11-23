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

"""ApiHarvester tasks."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask.globals import current_app

from .api import ApiHarvester


@shared_task(ignore_result=True)
def harvest_records(name, from_date=None, max=0, verbose=False):
    """Harvest records."""
    count = 0
    process_count = {}
    config = ApiHarvester(name)
    if config:
        if not from_date:
            from_date = config.lastrun

        count, process_count = config.get_records(from_date=from_date, max=max,
                                                  verbose=verbose)
    else:
        current_app.logger.warning(f'API Harvester name not found: {name}')
    return count, process_count
