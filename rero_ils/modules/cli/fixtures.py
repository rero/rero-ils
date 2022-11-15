# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2020 UCLouvain
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

"""Click command-line utilities."""

from __future__ import absolute_import, print_function

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from uuid import uuid4

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_jsonschemas.proxies import current_jsonschemas
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from jsonschema import validate
from werkzeug.local import LocalProxy

from ..collections.cli import create_collections
from ..holdings.cli import create_patterns
from ..ill_requests.cli import create_ill_requests
from ..items.cli import create_items, reindex_items
from ..loans.cli import create_loans, load_virtua_transactions
from ..operation_logs.cli import create_operation_logs, \
    destroy_operation_logs, dump_operation_logs
from ..patrons.cli import import_users
from ..providers import append_fixtures_new_identifiers
from ..utils import JsonWriter, bulk_load_metadata, bulk_load_pids, \
    bulk_load_pidstore, bulk_save_metadata, bulk_save_pids, \
    bulk_save_pidstore, csv_metadata_line, csv_pidstore_line, \
    get_record_class_from_schema_or_pid_type, get_schema_for_resource, \
    number_records_in_file, read_json_record

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)
_records_state = LocalProxy(lambda: current_app.extensions['invenio-records'])


@click.group()
def fixtures():
    """Fixtures management commands."""


fixtures.add_command(import_users)
fixtures.add_command(create_items)
fixtures.add_command(reindex_items)
fixtures.add_command(create_loans)
fixtures.add_command(load_virtua_transactions)
fixtures.add_command(create_patterns)
fixtures.add_command(create_ill_requests)
fixtures.add_command(create_collections)
fixtures.add_command(create_operation_logs)
fixtures.add_command(dump_operation_logs)
fixtures.add_command(destroy_operation_logs)


@fixtures.command('create')
@click.option('-u', '--create_or_update', 'create_or_update', is_flag=True,
              default=False)
@click.option('-a', '--append', 'append', is_flag=True, default=False)
@click.option('-r', '--reindex', 'reindex', is_flag=True, default=False)
@click.option('-c', '--dbcommit', 'dbcommit', is_flag=True, default=False)
@click.option('-C', '--commit', 'commit', default=100000)
@click.option('-v', '--verbose/--no-verbose', 'verbose',
              is_flag=True, default=True)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.option('-s', '--schema', 'schema', default=None)
@click.option('-t', '--pid_type', 'pid_type', default=None)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-o', '--dont-stop', 'dont_stop_on_error',
              is_flag=True, default=False)
@click.option('-P', '--pid-check', 'pid_check',
              is_flag=True, default=False)
@click.option('-e', '--save_errors', 'save_errors', type=click.File('w'))
@click.argument('infile', type=click.File('r'), default=sys.stdin)
@with_appcontext
def create(infile, create_or_update, append, reindex, dbcommit, commit,
           verbose, debug, schema, pid_type, lazy, dont_stop_on_error,
           pid_check, save_errors):
    """Load REROILS record.

    :param infile: Json file
    :param create_or_update: to update or create records.
    :param append: appends pids to database
    :param reindex: reindex record by record
    :param dbcommit: commit record to database
    :param commit: commit to database every count records
    :param pid_type: record type
    :param schema: recoord schema
    :param lazy: lazy reads file
    :param dont_stop_on_error: don't stop on error
    :param pidcheck: check pids
    :param save_errors: save error records to file
    """
    click.secho(
        f'Loading {pid_type} records from {infile.name}.',
        fg='green'
    )
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)

    if save_errors:
        errors = 0
        name, ext = os.path.splitext(infile.name)
        err_file_name = f'{name}_errors{ext}'
        error_file = JsonWriter(err_file_name)

    pids = []
    if lazy:
        # try to lazy read json file (slower, better memory management)
        records = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        records = json.load(infile)
    count = 0
    now = datetime.now(timezone.utc)
    order_date = now.strftime('%Y-%m-%d')
    year = str(now.year)
    for count, record in enumerate(records, 1):
        if pid_type == 'budg' and not record.get('name'):
            # ensure a budget is created for the current year
            record['name'] = year
            record['start_date'] = f'{year}-01-01'
            record['end_date'] = f'{year}-12-31'
        elif pid_type == 'acol' and record.pop('send_now', None):
            # ensure all orders are sent
            record['order_date'] = f'{order_date}'
        elif pid_type == 'acrl' and record.pop('receive_now', None):
            # ensure all receipt lines are received
            record['receipt_date'] = f'{order_date}'
        if schema:
            record['$schema'] = schema
        try:
            pid = record.get('pid')
            msg = 'created'
            db_record = record_class.get_record_by_pid(pid)
            if create_or_update and db_record:
                # case when record already exist in database
                db_record = record_class.get_record_by_pid(pid)
                rec = db_record.update(
                        record, dbcommit=dbcommit, reindex=reindex)
                msg = 'updated'
            elif create_or_update and pid and not db_record \
                    and record_class.record_pid_exists(pid):
                # case when record not in db but pid is reserved
                presist_id = PersistentIdentifier.get(
                    record_class.provider.pid_type, pid)
                rec = record_class.create(
                    record, dbcommit=dbcommit, reindex=reindex)
                if presist_id.status != PIDStatus.REGISTERED:
                    presist_id.register()
                    presist_id.assign(record_class.object_type, rec.id)
                msg = 'created'
            else:
                # case when record and pid are not in db
                rec = record_class.create(
                        record, dbcommit=dbcommit, reindex=reindex,
                        pidcheck=pid_check)
                if append:
                    pids.append(rec.pid)
            if verbose:
                click.echo(
                    f'{count: <8} {pid_type} {msg} {rec.pid}:{rec.id}')

        except Exception as err:
            pid = record.get('pid', '???')
            click.secho(
                f'{count: <8} {type} create error {pid}: {err}',
                fg='red'
            )
            if debug:
                traceback.print_exc()

            if save_errors:
                error_file.write(record)
            if not dont_stop_on_error:
                sys.exit(1)
        db.session.flush()
        if count > 0 and count % commit == 0:
            if verbose:
                click.echo(f'DB commit: {count}')
            db.session.commit()
    click.echo(f'DB commit: {count}')
    db.session.commit()

    if append:
        click.secho(f'Append fixtures new identifiers: {len(pids)}')
        identifier = record_class.provider.identifier
        try:
            append_fixtures_new_identifiers(
                identifier,
                sorted(pids, key=lambda x: int(x)),
                pid_type
            )
        except Exception as err:
            click.secho(
                f'ERROR append fixtures new identifiers: {err}',
                fg='red'
            )


@fixtures.command('count')
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'), default=sys.stdin)
def count_cli(infile, lazy):
    """Count records in file.

    :param infile: Json file
    :param lazy: lazy reads file
    :return: count of records
    """
    click.secho(
        f'Count records from {infile.name}.',
        fg='green'
    )
    if lazy:
        # try to lazy read json file (slower, better memory management)
        records = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        records = json.load(infile)
    count = 0
    for record in records:
        count += 1
    click.echo(f'Count: {count}')


@fixtures.command('create_csv')
@click.argument('record_type')
@click.argument('json_file')
@click.argument('output_directory')
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--create_pid', 'create_pid', is_flag=True, default=False)
@with_appcontext
def create_csv(record_type, json_file, output_directory, lazy, verbose,
               create_pid):
    """Create csv files from json.

    :param verbose: Verbose.
    """
    click.secho(
        f"Create CSV files for: {record_type} from: {json_file}",
        fg='green'
    )

    path = current_jsonschemas.url_to_path(
        get_schema_for_resource(record_type)
    )
    add_schema = get_schema_for_resource(record_type)
    schema = current_jsonschemas.get_schema(path=path)
    schema = _records_state.replace_refs(schema)
    count = 0
    errors_count = 0
    with open(json_file) as infile:
        if lazy:
            # try to lazy read json file (slower, better memory management)
            records = read_json_record(infile)
        else:
            # load everything in memory (faster, bad memory management)
            records = json.load(infile)

        file_name_pidstore = os.path.join(
            output_directory, f'{record_type}_pidstore.csv')
        click.secho(f'\t{file_name_pidstore}', fg='green')
        file_pidstore = open(file_name_pidstore, 'w')
        file_name_metadata = os.path.join(
            output_directory, f'{record_type}_metadata.csv'
        )
        click.secho(f'\t{file_name_metadata}', fg='green')
        file_metadata = open(file_name_metadata, 'w')
        file_name_pids = os.path.join(
            output_directory, f'{record_type}_pids.csv')
        click.secho(f'\t{file_name_pids}', fg='green')
        file_pids = open(file_name_pids, 'w')
        file_name_errors = os.path.join(
            output_directory, f'{record_type}_errors.json')
        file_errors = open(file_name_errors, 'w')
        file_errors.write('[')

        for count, record in enumerate(records, 1):
            pid = record.get('pid')
            if create_pid:
                pid = str(count)
                record['pid'] = pid
            uuid = str(uuid4())
            if verbose:
                click.secho(f'{count}\t{record_type}\t{pid}:{uuid}')
            date = str(datetime.utcnow())
            record['$schema'] = add_schema
            try:
                validate(record, schema)
                file_metadata.write(
                    csv_metadata_line(record, uuid, date)
                )
                file_pidstore.write(
                    csv_pidstore_line(record_type, pid, uuid, date)
                )
                file_pids.write(pid + '\n')
            except Exception as err:
                click.secho(
                    f'{count}\t{record_type}: Error validate in record: ',
                    fg='red')
                click.secho(str(err))
                if errors_count > 0:
                    file_errors.write(',')
                errors_count += 1
                file_errors.write('\n')
                for line in json.dumps(record, indent=2).split('\n'):
                    file_errors.write('  ' + line + '\n')

        file_pidstore.close()
        file_metadata.close()
        file_pids.close()
        file_errors.write('\n]')
        file_errors.close()
    if errors_count == 0:
        os.remove(file_name_errors)
    click.secho(
        f'Created: {count-errors_count} Errors: {errors_count}',
        fg='yellow'
    )


@fixtures.command('bulk_load')
@click.argument('record_type')
@click.argument('csv_metadata_file')
@click.option('-c', '--bulk_count', 'bulkcount', default=0, type=int,
              help='Set the bulk load chunk size.')
@click.option('-r', '--reindex', 'reindex', help='add record to reindex.',
              is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def bulk_load(record_type, csv_metadata_file, bulkcount, reindex, verbose):
    """Agency record management.

    :param csv_metadata_file: metadata: CSV file.
    :param bulk_count: Set the bulk load chunk size.
    :param reindex: add record to reindex.
    :param verbose: Verbose.
    """
    if bulkcount > 0:
        bulk_count = bulkcount
    else:
        bulk_count = current_app.config.get('BULK_CHUNK_COUNT', 100000)

    message = f'Load {record_type} CSV files into database.'
    click.secho(message, fg='green')
    file_name_metadata = csv_metadata_file
    file_name_pidstore = file_name_metadata.replace('metadata', 'pidstore')
    file_name_pids = file_name_metadata.replace('metadata', 'pids')

    record_counts = number_records_in_file(file_name_pidstore, 'csv')
    message = f'  Number of records to load: {record_counts}'
    click.secho(message, fg='green')

    click.secho(f'  Load pids: {file_name_pids}')
    bulk_load_pids(pid_type=record_type, ids=file_name_pids,
                   bulk_count=bulk_count, verbose=verbose)
    click.secho(f'  Load pidstore: {file_name_pidstore}')
    bulk_load_pidstore(pid_type=record_type, pidstore=file_name_pidstore,
                       bulk_count=bulk_count, verbose=verbose)
    click.secho(f'  Load metatada: {file_name_metadata}')
    bulk_load_metadata(pid_type=record_type, metadata=file_name_metadata,
                       bulk_count=bulk_count, verbose=verbose, reindex=reindex)


@fixtures.command('bulk_save')
@click.argument('output_directory')
@click.option('-t', '--pid_types', multiple=True, default=['all'])
@click.option('-d', '--deployment', 'deployment', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def bulk_save(pid_types, output_directory, deployment, verbose):
    """Record dump.

    :param pid_type: Records to export.
        default=//all//
    :param verbose: Verbose.
    """
    file_name_tmp_pidstore = os.path.join(
        output_directory,
        'tmp_pidstore.csv'
    )
    try:
        os.remove(file_name_tmp_pidstore)
    except OSError:
        pass

    all_pid_types = []
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS')
    for endpoint in endpoints:
        all_pid_types.append(endpoint)
    if pid_types[0] == 'all':
        pid_types = all_pid_types

    for p_type in pid_types:
        if p_type not in all_pid_types:
            click.secho(
                f'Error {p_type} does not exist!',
                fg='red'
            )
            continue
        # TODO: do we have to save loanid and how we can save it?
        if p_type in ['loanid', 'oplg']:
            continue
        click.secho(
            f'Save {p_type} CSV files to directory: {output_directory}',
            fg='green'
        )
        file_prefix = endpoints[p_type].get('search_index')
        if p_type in ['doc', 'hold', 'item', 'count']:
            if deployment:
                file_prefix += '_big'
            else:
                file_prefix += '_small'
        file_name_metadata = os.path.join(
            output_directory,
            f'{file_prefix}_metadata.csv'
        )
        bulk_save_metadata(pid_type=p_type, file_name=file_name_metadata,
                           verbose=verbose)
        file_name_pidstore = os.path.join(
            output_directory,
            f'{file_prefix}_pidstore.csv'
        )
        count = bulk_save_pidstore(pid_type=p_type,
                                   file_name=file_name_pidstore,
                                   file_name_tmp=file_name_tmp_pidstore,
                                   verbose=verbose)

        file_name_pids = os.path.join(
            output_directory,
            f'{file_prefix}_pids.csv'
        )
        bulk_save_pids(pid_type=p_type, file_name=file_name_pids,
                       verbose=verbose)
        click.secho(
            f'Saved records: {count}',
            fg='yellow'
        )
    try:
        os.remove(file_name_tmp_pidstore)
    except OSError:
        pass
