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

from datetime import date

from celery import shared_task
from flask import current_app

from rero_ils.modules.stats.api import Stat, StatsForLibrarian, \
    StatsForPricing, StatsReport
from rero_ils.modules.stats_cfg.api import StatsConfigurationSearch


@shared_task()
def collect_stats_billing():
    """Collect and store the statistics for billing."""
    stats_pricing = StatsForPricing().collect()
    with current_app.app_context():
        stat = Stat.create(
            dict(type='billing', values=stats_pricing),
            dbcommit=True, reindex=True)
        return f'New statistics of type {stat["type"]} has\
            been created with a pid of: {stat.pid}'


@shared_task()
def collect_stats_librarian():
    """Collect and store the montly statistics for librarian."""
    stats_librarian = StatsForLibrarian()
    date_range = {'from': stats_librarian.date_range['gte'],
                  'to': stats_librarian.date_range['lte']}
    stats_values = stats_librarian.collect()
    with current_app.app_context():
        stat = Stat.create(
            dict(type='librarian', date_range=date_range,
                 values=stats_values),
            dbcommit=True, reindex=True)
        return f'New statistics of type {stat["type"]} has\
            been created with a pid of: {stat.pid}'


@shared_task()
def collect_stats_report():
    """Create the montly and yearly statistics reports."""
    today = date.today()
    if today.day != 1:
        return
    with current_app.app_context():
        pids = []
        cfg_pids = get_stats_config_to_execute(today)
        for cfg_pid in cfg_pids:
            stats_report = StatsReport()\
                           .create(cfg_pid, dbcommit=True, reindex=True)
            if stats_report:
                pids.append(stats_report.pid)

        if pids:
            return f'New statistics of type report '\
                    f'has been created with pids: {", ".join(pids)}.'


def get_stats_config_to_execute(today):
    """Statistics configurations to execute today.

    :param today: date of today
    :returns: list of configuration pids
    """
    stats_cfgs = StatsConfigurationSearch.get_active_stats_configurations()

    cfg_pids = []
    for cfg in stats_cfgs:
        if (cfg['frequency'] == 'month' or
           (cfg['frequency'] == 'year' and today.month == 1)):
            cfg_pids.append(cfg.pid)
    return cfg_pids
