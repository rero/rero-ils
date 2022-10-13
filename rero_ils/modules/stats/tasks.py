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

from datetime import date

from celery import shared_task
from flask import current_app

from rero_ils.modules.stats.api import Stat, StatsForLibrarian, \
    StatsForPricing, StatsReport
from rero_ils.modules.stats_cfg.api import Stat_cfg


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
    """Collect and store the statistics for report."""
    today = date.today()
    if today.day == 1:
        with current_app.app_context():
            cfgs = Stat_cfg.get_cfgs()
            msg = ''
            for cfg in cfgs:
                if cfg['status'] == 'active' and \
                   (cfg['frequency'] == 'month' or
                   (today.month == 1 and cfg['frequency'] == 'year')):
                    stat = StatsReport().create(cfg['pid'],
                                                dbcommit=True, reindex=True)
                    if stat:
                        msg += f'New statistics of type {stat["type"]} has\
                                been created with a pid of: {stat.pid}\n'
            return msg
