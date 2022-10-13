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

"""Click command-line interface for operation logs."""

import json
from pprint import pprint

import arrow
import click
from dateutil.relativedelta import relativedelta
from flask import current_app
from flask.cli import with_appcontext

from rero_ils.modules.stats.api import Stat, StatsForLibrarian, \
    StatsForPricing, StatsReport
from rero_ils.modules.stats_cfg.api import Stat_cfg


@click.group()
def stats():
    """Notification management commands."""


@stats.command('dumps')
@click.argument('type')
@with_appcontext
def dumps(type):
    """Dumps the current stats value.

    :param type: type of statistics can be 'billing' or 'librarian'
    """
    if type == 'billing':
        pprint(StatsForPricing(to_date=arrow.utcnow()).collect(), indent=2)
    elif type == 'librarian':
        pprint(StatsForLibrarian(to_date=arrow.utcnow()).collect(), indent=2)


@stats.command('collect')
@click.argument('type')
@with_appcontext
def collect(type):
    """Extract the stats value and store it.

    :param type: type of statistics can be 'billing' or 'librarian'
    """
    to_date = arrow.utcnow() - relativedelta(days=1)
    date_range = {}
    if type == 'billing':
        _stats = StatsForPricing(to_date=to_date)
    elif type == 'librarian':
        _from = f'{to_date.year}-{to_date.month:02d}-01T00:00:00'
        _to = to_date.format(fmt='YYYY-MM-DDT23:59:59')
        date_range = {'from': _from, 'to': _to}
        _stats = StatsForLibrarian(to_date=to_date)
    else:
        return

    stats_values = _stats.collect()
    with current_app.app_context():
        stat = Stat.create(
                dict(type=type, date_range=date_range,
                     values=stats_values),
                dbcommit=True, reindex=True)
        click.secho(
            f'Statistics of type {stat["type"]}\
            have been collected and created.\
            New pid: {stat.pid}', fg='green')


@stats.command('collect_year')
@click.argument('year', type=int)
@click.argument('timespan', default='yearly')
@click.option('--n_months', default=12)
@click.option('-f', '--force', is_flag=True, default=False)
@with_appcontext
def collect_year(year, timespan, n_months, force):
    """Extract the stats librarian for one year and store them in db.

    :param year: year of statistics
    :param n_months: month up to which the statistics are calculated
    :param timespan: time interval, can be 'montly' or 'yearly'
    :param force: force update of stat.
    """
    stat_pid = None
    type = 'librarian'
    if year:
        if timespan == 'montly':
            if n_months not in range(1, 13):
                click.secho(f'ERROR: not a valid month', fg='red')
                raise click.Abort()
            n_months += 1

            for month in range(1, n_months):
                first_day = f'{year}-{month:02d}-01T23:59:59'\
                            .format(fmt='YYYY-MM-DDT23:59:59')
                first_day = arrow.get(first_day, 'YYYY-MM-DDTHH:mm:ss')
                to_date = first_day + relativedelta(months=1)\
                    - relativedelta(days=1)
                _from = f'{to_date.year}-{to_date.month:02d}-01T00:00:00'
                _to = to_date.format(fmt='YYYY-MM-DDT23:59:59')

                date_range = {'from': _from, 'to': _to}

                _stats = StatsForLibrarian(to_date=to_date)

                stat_pid = _stats.get_stat_pid(type, date_range)

                if stat_pid and not force:
                    click.secho(
                            f'ERROR: statistics of type {type}\
                                for time interval {_from} - {_to}\
                                already exist. Pid: {stat_pid}', fg='red')
                    return

                stat_data = dict(type=type, date_range=date_range,
                                 values=_stats.collect())

                with current_app.app_context():
                    if stat_pid:
                        rec_stat = Stat.get_record_by_pid(stat_pid)
                        stat = rec_stat.update(data=stat_data, commit=True,
                                               dbcommit=True, reindex=True)
                        click.secho(
                            f'WARNING: statistics of type {type}\
                                have been collected and updated\
                                for {year}-{month}.\
                                Pid: {stat.pid}', fg='yellow')
                    else:
                        stat = Stat.create(stat_data, dbcommit=True,
                                           reindex=True)
                        click.secho(
                            f'Statistics of type {type} have been collected\
                                and created for {year}-{month}.\
                                New pid: {stat.pid}', fg='green')
        else:
            _from = arrow.get(f'{year}-01-01', 'YYYY-MM-DD')\
                         .format(fmt='YYYY-MM-DDT00:00:00')
            _to = arrow.get(f'{year}-12-31', 'YYYY-MM-DD')\
                       .format(fmt='YYYY-MM-DDT23:59:59')
            date_range = {'from': _from, 'to': _to}

            _stats = StatsForLibrarian()

            _stats.date_range = {'gte': _from, 'lte': _to}

            stat_pid = _stats.get_stat_pid(type, date_range)
            if stat_pid and not force:
                click.secho(
                    f'ERROR: statistics of type {type}\
                        for time interval {_from} - {_to}\
                        already exist. Pid: {stat_pid}', fg='red')
                return

            stat_data = dict(type=type, date_range=date_range,
                             values=_stats.collect())

            with current_app.app_context():
                if stat_pid:
                    rec_stat = Stat.get_record_by_pid(stat_pid)
                    stat = rec_stat.update(data=stat_data, commit=True,
                                           dbcommit=True, reindex=True)
                    click.secho(
                        f'WARNING: statistics of type {type}\
                            have been collected and updated for {year}.\
                            Pid: {stat.pid}', fg='yellow')
                else:
                    stat = Stat.create(stat_data, dbcommit=True, reindex=True)
                    click.secho(
                        f'Statistics of type {type} have been collected and\
                            created for {year}.\
                            New pid: {stat.pid}', fg='green')

        return


@stats.command('report_cfg')
@click.argument('data')
@with_appcontext
def report_cfg(data):
    """Create statistics configuration for report.

    :param data: configuration data
    """
    with current_app.app_context():
        data = json.loads(data)
        stat = Stat_cfg.create(data, dbcommit=True, reindex=True)
        click.secho(
            f'Statistics configuration has been created.\
            New configuration pid: {stat.pid}', fg='green')


@stats.command('report')
@click.argument('pid', type=str)
@with_appcontext
def report(pid):
    """Create statistics report.

    :param pid: configuration pid
    """
    with current_app.app_context():
        stat = StatsReport().create(pid, dbcommit=True, reindex=True)
        click.secho(
            f'Statistics report has been created for configuration pid {pid}.\
            New report pid: {stat.pid}', fg='green')
