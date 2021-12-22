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


from pprint import pprint

import arrow
import click
from dateutil.relativedelta import relativedelta
from flask.cli import with_appcontext

from rero_ils.modules.stats.api import Stat, StatsForLibrarian, StatsForPricing


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
    stat = Stat.create(
            dict(type=type, date_range=date_range, values=_stats.collect()),
            dbcommit=True, reindex=True)
    click.secho(
        f'Statistics of type {stat["type"]} have been collected and created.\
        New pid: {stat.pid}', fg='green')


@stats.command('collect_year')
@click.argument('type')
@click.argument('year', type=int)
@click.argument('timespan', default='yearly')
@with_appcontext
def collect_year(type, year, timespan):
    """Extract the stats values for one year and store them in db.

    :param type: type of statistics can be 'billing' or 'librarian'
    :param year: year of statistics
    """
    if year:
        if timespan == 'montly':
            for month in range(1, 13):
                first_day = f'{year}-{month:02d}-01T23:59:59'\
                            .format(fmt='YYYY-MM-DDT23:59:59')
                first_day = arrow.get(first_day, 'YYYY-MM-DDTHH:mm:ss')
                to_date = first_day + relativedelta(months=1)\
                    - relativedelta(days=1)
                _from = f'{to_date.year}-{to_date.month:02d}-01T00:00:00'
                _to = to_date.format(fmt='YYYY-MM-DDT23:59:59')
                date_range = {'from': _from, 'to': _to}

                if type == 'billing':
                    _stats = StatsForPricing(to_date=to_date)
                elif type == 'librarian':
                    _stats = StatsForLibrarian(to_date=to_date)
                else:
                    return
                stat = Stat.create(
                        dict(type=type, date_range=date_range,
                             values=_stats
                             .collect()), dbcommit=True, reindex=True)
                click.secho(
                    f'Statistics of type {stat["type"]} have been collected\
                        and created for {year}-{month}.\
                        New pid: {stat.pid}', fg='green')
        else:
            _from = arrow.get(f'{year}-01-01', 'YYYY-MM-DD')\
                         .format(fmt='YYYY-MM-DDT00:00:00')
            _to = arrow.get(f'{year}-12-31', 'YYYY-MM-DD')\
                       .format(fmt='YYYY-MM-DDT23:59:59')
            date_range = {'from': _from, 'to': _to}

            if type == 'billing':
                _stats = StatsForPricing()
            elif type == 'librarian':
                _stats = StatsForLibrarian()
            else:
                return

            _stats.date_range = date_range
            stat = Stat.create(
                    dict(type=type, date_range=date_range,
                         values=_stats.collect()), dbcommit=True, reindex=True)
            click.secho(
                f'Statistics of type {stat["type"]} have been collected and\
                    created for {year}.\
                    New pid: {stat.pid}', fg='green')

        return
