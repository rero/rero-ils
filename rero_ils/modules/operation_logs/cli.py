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

"""Click command-line interface for operation_log record management."""

from __future__ import absolute_import, print_function

import json

import click
from flask import current_app
from flask.cli import with_appcontext

from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.operation_logs.models import OperationLogOperation
from rero_ils.modules.utils import extracted_data_from_ref

from ..utils import read_json_record


@click.command('migrate_virtua_operation_logs')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def migrate_virtua_operation_logs(infile, verbose, debug, lazy):
    """Migrate Virtua operation log records in reroils.

    :param infile: Json operation log file.
    :param lazy: lazy reads file
    """
    enabled_logs = current_app.config.get('RERO_ILS_ENABLE_OPERATION_LOG')
    click.secho('Migrate Virtua operation log records:', fg='green')
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        data = json.load(infile)
    index_count = 0
    with click.progressbar(data) as bar:
        for oplg in bar:
            try:
                operation = oplg.get('operation')
                resource = extracted_data_from_ref(
                    oplg.get('record').get('$ref'), data='resource')
                pid_type = enabled_logs.get(resource)
                if pid_type and operation == OperationLogOperation.CREATE:
                    # The virtua create operation log overrides the reroils
                    # create operation log, the method to use is UPDATE
                    record_pid = extracted_data_from_ref(
                        oplg.get('record').get('$ref'), data='pid')

                    create_rec = \
                        OperationLog.get_create_operation_log_by_resource_pid(
                            pid_type, record_pid)
                    if create_rec:
                        create_rec.update(oplg, dbcommit=True, reindex=True)
                elif pid_type and operation == OperationLogOperation.UPDATE:
                    # The virtua update operation log is a new entry in the
                    # reroils operation log, the method to use is CREATE
                    OperationLog.create(data=oplg, dbcommit=True, reindex=True)
            except Exception:
                pass
        index_count += len(data)
    click.echo('created {index_count} operation logs.'.format(
        index_count=index_count))
