# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Celery tasks for stats records."""

from celery import shared_task

from .api import Stat, StatsForPricing


@shared_task()
def collect_stats():
    """Collect and store the current statistics."""
    stats_for_pricing = StatsForPricing()
    stat = Stat.create(
        dict(values=stats_for_pricing.collect()), dbcommit=True, reindex=True)
    return f'New stat has been created with a pid of: {stat.pid}'
