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

"""Click command-line interface for operation_log record management."""

from __future__ import absolute_import, print_function

import json

import click
from flask.cli import with_appcontext
from invenio_search.api import RecordsSearch

from rero_ils.modules.operation_logs.api import OperationLog

from ..utils import JsonWriter, read_json_record


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.command('create_operation_logs')
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-s', '--batch-size', 'size', type=int, default=10000)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def create_operation_logs(infile, lazy, size):
    """Load operation log records in reroils.

    :param infile: Json operation log file.
    :param lazy: lazy reads file
    """
    click.secho('Load operation log records:', fg='green')
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        data = json.load(infile)
    index_count = 0
    with click.progressbar(data) as bar:
        records = []
        for oplg in bar:
            if not (index_count + 1) % size:
                OperationLog.bulk_index(records)
                records = []
            records.append(oplg)
            index_count += 1
        # the rest of the records
        if records:
            OperationLog.bulk_index(records)
            index_count += len(records)
    click.echo(f'created {index_count} operation logs.')


@click.command('dump_operation_logs')
@click.argument('outfile_name')
@click.option('-y', '--year', 'year', type=int)
@with_appcontext
def dump_operation_logs(outfile_name, year):
    """Dumps operation log records in a given file.

    :param outfile: JSON operation log output file.
    """
    click.secho('Dumps operation log records:', fg='green')
    index_name = OperationLog.index_name
    if year is not None:
        index_name = f'{index_name}-{year}'
    search = RecordsSearch(index=index_name)

    index_count = 0
    outfile = JsonWriter(outfile_name)
    with click.progressbar(search.scan(), length=search.count()) as bar:
        for oplg in bar:
            outfile.write(str(oplg.to_dict()))
            index_count += 1
    click.echo(f'created {index_count} operation logs.')


@click.command('destroy_operation_logs')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to remove all the operation logs?')
@with_appcontext
def destroy_operation_logs():
    """Removes all the operation logs data."""
    OperationLog.delete_indices()
    click.secho('All operations logs have been removed', fg='green')
