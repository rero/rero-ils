# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

from .models import ApiHarvestConfig
from .utils import get_records


@shared_task(ignore_result=True)
def harvest_records(url=None, name=None, from_date=None, signals=True, size=0,
                    max_results=0, verbose=False):
    """Harvest records."""
    config = ApiHarvestConfig.query.filter_by(name=name).first()
    if config:
        if not url:
            url = config.url
        if not from_date:
            from_date = config.lastrun
            config.update_lastrun()
        if size == 0:
            size = config.size

    for next, records in get_records(
        url=url, name=name, from_date=from_date, size=size,
        max_results=max_results, signals=signals, verbose=verbose
    ):
        pass
