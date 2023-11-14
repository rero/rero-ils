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

"""Celery tasks for stats records."""

from celery import shared_task
from flask import current_app

from rero_ils.modules.stats_cfg.api import StatConfiguration, \
    StatsConfigurationSearch

from .api.api import Stat
from .api.librarian import StatsForLibrarian
from .api.pricing import StatsForPricing
from .api.report import StatsReport
from .models import StatType


@shared_task()
def collect_stats_billing():
    """Collect and store the statistics for billing."""
    stats_pricing = StatsForPricing().collect()
    with current_app.app_context():
        stat = Stat.create(
            dict(type=StatType.BILLING, values=stats_pricing),
            dbcommit=True, reindex=True)
        return f'New statistics of type {stat["type"]} has\
            been created with a pid of: {stat.pid}'


@shared_task()
def collect_stats_librarian():
    """Collect and store the monthly statistics for librarian."""
    stats_librarian = StatsForLibrarian()
    date_range = {'from': stats_librarian.date_range['gte'],
                  'to': stats_librarian.date_range['lte']}
    stats_values = stats_librarian.collect()
    with current_app.app_context():
        stat = Stat.create(
            dict(type=StatType.LIBRARIAN, date_range=date_range,
                 values=stats_values),
            dbcommit=True, reindex=True)
        return f'New statistics of type {stat["type"]} has\
            been created with a pid of: {stat.pid}'


@shared_task()
def collect_stats_reports(frequency='month'):
    """Collect and store the montly statistics for librarian."""
    pids = [
        hit.pid for hit in
        StatsConfigurationSearch().filter(
            'term', frequency=frequency).source('pid').scan()
    ]
    to_return = []
    logger = current_app.logger
    for pid in pids:
        try:
            cfg = StatConfiguration.get_record_by_pid(pid)
            stat_report = StatsReport(cfg)
            values = stat_report.collect()
            report = stat_report.create_stat(values)
            to_return.append(report.pid)
        except Exception as error:
            logger.error(
                f'Unable to generate report from config({pid}) :: {error}',
                exc_info=True, stack_info=True
            )
    return to_return
