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

"""Click command-line interface for operation logs."""


from pprint import pprint

import arrow
import click
from dateutil.relativedelta import relativedelta
from flask import current_app
from flask.cli import with_appcontext

from .api.api import Stat
from .api.librarian import StatsForLibrarian
from .api.pricing import StatsForPricing
from .models import StatType


@click.group()
def stats():
    """Statistics management commands."""


@stats.group()
def report():
    """Stats report management commands."""


@stats.command()
@click.argument('type')
@with_appcontext
def dumps(type):
    """Dumps the current stats value.

    :param type: type of statistics can be 'billing' or 'librarian'
    """
    if type == StatType.BILLING:
        pprint(StatsForPricing(to_date=arrow.utcnow()).collect(), indent=2)
    elif type == StatType.LIBRARIAN:
        pprint(StatsForLibrarian(to_date=arrow.utcnow()).collect(), indent=2)


@stats.command()
@click.argument('type')
@with_appcontext
def collect(type):
    """Extract the stats values and store it.

    :param type: type of statistics can be 'billing' or 'librarian'
    """
    to_date = arrow.utcnow() - relativedelta(days=1)
    date_range = {}
    if type == StatType.BILLING:
        _stats = StatsForPricing(to_date=to_date)
    elif type == StatType.LIBRARIAN:
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


@stats.command()
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
    type = StatType.LIBRARIAN
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


@report.command()
@click.argument('pid')
@with_appcontext
def dumps(pid):
    """Extract the stats value for preview.

    :param pid: pid value of the configuration to use.
    """
    from .api.report import StatsReport
    from ..stats_cfg.api import StatConfiguration
    cfg = StatConfiguration.get_record_by_pid(pid)
    if not cfg:
        click.secho(f'Configuration does not exists.', fg='red')
    else:
        from pprint import pprint
        pprint(StatsReport(cfg).collect())


@report.command()
@click.argument('pid')
@with_appcontext
def collect(pid):
    """Extract the stats report values and store it.

    :param pid: pid value of the configuration to use.
    """
    from .api.report import StatsReport
    from ..stats_cfg.api import StatConfiguration
    cfg = StatConfiguration.get_record_by_pid(pid)
    if not cfg:
        click.secho(f'Configuration does not exists.', fg='red')
    else:
        stat_report = StatsReport(cfg)
        values = stat_report.collect()
        stat_report.create_stat(values)


@report.command()
@click.argument('frequency', type=click.Choice(['month', 'year']))
@click.option('--delayed', '-d', is_flag=True,
              help='Run indexing in background.')
@with_appcontext
def collect_all(frequency, delayed):
    """Extract the stats report values and store it.

    :param pid: pid value of the configuration to use.
    """
    from .tasks import collect_stats_reports
    if delayed:
        res = collect_stats_reports.delay(frequency)
        click.secho(f'Generated reports delayed, task id: {res}', fg='green')
    else:
        res = collect_stats_reports(frequency)
        click.secho(f'Generated {len(res)} reports.', fg='green')
