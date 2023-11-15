# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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
import sys

import click
import dateparser
from celery.messaging import establish_connection
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_rest.utils import obj_or_import_string
from invenio_search.cli import index, search_version_check
from invenio_search.proxies import current_search, current_search_client
from jsonpatch import make_patch
from kombu import Queue

from .utils import get_record_class_from_schema_or_pid_type
from ..api import IlsRecordsIndexer
from ..monitoring.api import Monitoring
from ..tasks import process_bulk_queue


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


def connect_queue(connection, name):
    """Queue establish connection or create queue.

    :param name: Name for queue, if None the INDEXER_MQ_QUEUE is used.
    :returns: connected queue.
    """
    if name:
        exchange = current_app.config.get('INDEXER_MQ_EXCHANGE')
        exchange = exchange(connection)
        queue = Queue(name, exchange=exchange, routing_key=name)
    else:
        queue = current_app.config['INDEXER_MQ_QUEUE']
    connected_queue = queue(connection)
    return connected_queue


@click.group()
def index():
    """Index management commands."""


@index.command()
@click.option('--delayed', '-d', is_flag=True,
              help='Run indexing in background.')
@click.option('--concurrency', '-c', default=1, type=int,
              help='Number of concurrent indexing tasks to start.')
@click.option('--with_stats', is_flag=True, default=False,
              help='report number of success and list failed error response.')
@click.option('--queue', '-q', type=str, default=None,
              help='Name of the celery queue used to put the tasks into.')
@click.option('--version-type', help='Elasticsearch version type to use.')
@click.option('--raise-on-error/--skip-errors', default=True,
              help='Controls if ES bulk indexing errors raise an exception.')
@with_appcontext
def run(delayed, concurrency, with_stats, version_type=None, queue=None,
        raise_on_error=True):
    """Run bulk record indexing."""
    if delayed:
        click.secho(
            f'Starting {concurrency} tasks for indexing records '
            f'({queue})...',
            fg='green'
        )
        celery_kwargs = {
            'kwargs': {
                'version_type': version_type,
                'queue': queue,
                'search_bulk_kwargs': {'raise_on_error': raise_on_error},
                'stats_only': not with_stats
            }
        }
        for _ in range(0, concurrency):
            process_id = process_bulk_queue.apply_async(**celery_kwargs)
            click.secho(f'Index async ({queue}): {process_id}', fg='yellow')

    else:
        if queue:
            click.secho(f'Indexing records ({queue})...', fg='green')
        else:
            click.secho(f'Indexing records ...', fg='green')
        connected_queue = None
        if queue:
            connection = establish_connection()
            connected_queue = connect_queue(connection, queue)
        indexer = IlsRecordsIndexer(
            version_type=version_type,
            queue=connected_queue,
            routing_key=queue,
        )
        name, count = indexer.process_bulk_queue(
                search_bulk_kwargs={'raise_on_error': raise_on_error},
                stats_only=(not with_stats)
            )
        click.secho(
            f'"{name}" indexed: {count[0]} error: {count[1]}', fg='yellow')


@index.command()
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to reindex records?')
@click.option('-t', '--pid-types', multiple=True)
@click.option('-f', '--from_date', 'from_date')
@click.option('-u', '--until_date', 'until_date')
@click.option('-d', '--direct', 'direct', is_flag=True, default=False)
@click.option('-q', '--queue', 'queue', default='indexer')
@with_appcontext
def reindex(pid_types, from_date, until_date, direct, queue):
    """Reindex records.

    :param pid_type: Pid type.
    :param from_date: Index records from date.
    :param until_date: Index records until date.
    :param direct: Use record class for indexing.
    :param queue: Queue name to use.
    """
    endpoints = current_app.config.get('RECORDS_REST_ENDPOINTS')
    if not pid_types:
        pid_types = list(endpoints)
    for pid_type in pid_types:
        if pid_type in endpoints:
            msg = f'Sending {pid_type} to indexing queue '
            msg += f'({queue}): ' if queue else ': '
            if direct:
                msg = f'Indexing {pid_type}: '
            click.secho(msg, fg='green', nl=False)
            query = None
            record_cls = obj_or_import_string(
                endpoints[pid_type].get('record_class'))
            if from_date or until_date:
                model_cls = record_cls.model_cls
                if model_cls != RecordMetadata:
                    query = model_cls.query \
                        .filter(model_cls.is_deleted.is_(False)) \
                        .with_entities(model_cls.id) \
                        .order_by(model_cls.created)
                    if from_date:
                        query = query.filter(
                            model_cls.updated > dateparser.parse(from_date))
                    if until_date:
                        query = query.filter(
                            model_cls.updated <= dateparser.parse(until_date))
            else:
                query = PersistentIdentifier.query \
                    .filter_by(object_type='rec', status=PIDStatus.REGISTERED)\
                    .filter_by(pid_type=pid_type) \
                    .with_entities(PersistentIdentifier.object_uuid)
            if query:
                click.echo(f'{query.count()}')
                if direct:
                    for idx, id in enumerate((x[0] for x in query), 1):
                        msg = f'{idx}\t{id}\t'
                        try:
                            rec = record_cls.get_record(id)
                            msg += f'{rec.pid}'
                            rec.reindex()
                        except Exception as err:
                            msg += f'\t{err}'
                        click.echo(msg)
                else:
                    exchange = current_app.config.get('INDEXER_MQ_EXCHANGE')
                    simple_queue = Queue(
                        queue, exchange=exchange, routing_key=queue)
                    indxer = IlsRecordsIndexer(
                        queue=simple_queue, routing_key=queue)
                    indxer.bulk_index(
                        (x[0] for x in query), doc_type=pid_type)
            else:
                click.echo('Can not index by date.')
        else:
            click.secho(f'ERROR type does not exist: {pid_type}', fg='red')
        if not direct:
            msg = 'Execute "invenio reroils index run'
            if queue != 'indexer':
                msg = f'{msg} -q {queue}'
            msg = f'{msg}" command to process the queue!'
            click.secho(msg, fg='yellow')


@index.command('reindex_missing')
@click.option('-t', '--pid-types', multiple=True, required=True)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def reindex_missing(pid_types, verbose):
    """Index all missing records.

    :param pid_type: Pid type.
    """
    for p_type in pid_types:
        click.secho(
            f'Indexing missing {p_type}: ',
            fg='green',
            nl=False
        )
        record_class = get_record_class_from_schema_or_pid_type(
            pid_type=p_type
        )
        if not record_class:
            click.secho(
                'ERROR pid type does not exist!',
                fg='red',
            )
            continue
        monitoring = Monitoring(time_delta=0)
        pids_es, pids_db, pids_es_double, index = \
            monitoring.get_es_db_missing_pids(p_type)
        click.secho(
            f'{len(pids_db)}',
            fg='green',
        )
        for idx, pid in enumerate(pids_db, 1):
            record = record_class.get_record_by_pid(pid)
            if record:
                record.reindex()
                if verbose:
                    click.secho(f'{idx}\t{p_type}\t{pid}')
            else:
                if verbose:
                    click.secho(f'NOT FOUND: {idx}\t{p_type}\t{pid}', fg='red')


@index.command()
@click.option('--force', is_flag=True, default=False)
@with_appcontext
@search_version_check
def init(force):
    """Initialize registered templates, aliases and mappings."""
    # TODO: to remove once it is fixed in invenio-search module
    click.secho('Putting templates...', fg='green', bold=True, file=sys.stderr)
    with click.progressbar(
            current_search.put_templates(ignore=[400] if force else None),
            length=len(current_search.templates)) as bar:
        for response in bar:
            bar.label = response
    click.secho('Creating indexes...', fg='green', bold=True, file=sys.stderr)
    with click.progressbar(
            current_search.create(ignore=[400] if force else None),
            length=len(current_search.mappings)) as bar:
        for name, response in bar:
            bar.label = name


@index.command('switch_index')
@with_appcontext
@search_version_check
@click.argument('old')
@click.argument('new')
def switch_index(old, new):
    """Switch index using the elasticsearch aliases.

    :param old: full name of the old index
    :param new: full name of the fresh created index
    """
    aliases = current_search_client.indices.get_alias().get(old)\
        .get('aliases').keys()
    for alias in aliases:
        current_search_client.indices.put_alias(new, alias)
        current_search_client.indices.delete_alias(old, alias)
    click.secho('Sucessfully switched.', fg='green')


@index.command('create_index')
@with_appcontext
@search_version_check
@click.option(
    '-t', '--templates/--no-templates', 'templates', is_flag=True,
    default=True)
@click.option(
    '-v', '--verbose/--no-verbose', 'verbose', is_flag=True, default=False)
@click.argument('resource')
@click.argument('index')
def create_index(resource, index, verbose, templates):
    """Create a new index based on the mapping of a given resource.

    :param resource: the resource such as documents.
    :param index: the index name such as documents-document-v0.0.1-20211014
    :param verbose: display addtional message.
    :param templates: update also the es templates.
    """
    if templates:
        tbody = current_search_client.indices.get_template()
        for tmpl in current_search.put_templates():
            click.secho(f'file:{tmpl[0]}, ok: {tmpl[1]}', fg='green')
            new_tbody = current_search_client.indices.get_template()
            patch = make_patch(new_tbody, tbody)
            if patch:
                click.secho('Templates are updated.', fg='green')
                if verbose:
                    click.secho('Diff in templates', fg='green')
                    click.echo(patch)
            else:
                click.secho('Templates did not changed.', fg='yellow')

    f_mapping = [
        v for v in current_search.aliases.get(resource).values()].pop()
    mapping = json.load(open(f_mapping))
    current_search_client.indices.create(index, mapping)
    click.secho(f'Index {index} has been created.', fg='green')


@index.command('update_mapping')
@click.option('--aliases', '-a', multiple=True, help='all if not specified')
@click.option(
    '-s', '--settings/--no-settings', 'settings', is_flag=True, default=False)
@with_appcontext
@search_version_check
def update_mapping(aliases, settings):
    """Update the mapping of a given alias."""
    if not aliases:
        aliases = current_search.aliases.keys()
    for alias in aliases:
        for index, f_mapping in iter(
            current_search.aliases.get(alias).items()
        ):
            mapping = json.load(open(f_mapping))
            try:
                if mapping.get('settings') and settings:
                    current_search_client.indices.close(index=index)
                    current_search_client.indices.put_settings(
                        body=mapping.get('settings'), index=index)
                    current_search_client.indices.open(index=index)
                res = current_search_client.indices.put_mapping(
                    body=mapping.get('mappings'), index=index)
            except Exception as excep:
                click.secho(
                    f'error: {excep}', fg='red')
            if res.get('acknowledged'):
                click.secho(
                    f'index: {index} has been sucessfully updated', fg='green')
            else:
                click.secho(
                    f'error: {res}', fg='red')


@index.group()
def queue():
    """Manage indexing queue."""


@queue.command('init')
@click.option('-n', '--name', default=None)
@with_appcontext
def init_queue(name):
    """Initialize indexing queue.

    :papram name: Name of queue.
    """
    with establish_connection() as connection:
        queue = connect_queue(connection, name)
        result = queue.declare()
        click.secho(
            f'Queue has been initialized: {result}',
            fg='green'
        )


@queue.command('purge')
@click.option('-n', '--name', default=None)
@with_appcontext
def purge_queue(name):
    """Purge indexing queue.

    :papram name: Name of queue.
    """
    with establish_connection() as connection:
        queue = connect_queue(connection, name)
        try:
            result = queue.purge()
        except Exception as err:
            result = err
        click.secho(
            f'Queue has been purged: {queue.name} {result}',
            fg='green'
        )


@queue.command('delete')
@click.option('-n', '--name', default=None)
@click.option('-f', '--force', is_flag=True, default=True)
@with_appcontext
def delete_queue(name, force):
    """Delete indexing queue.

    :papram name: Name of queue.
    :papram force: Force delete the queue.
    """
    with establish_connection() as connection:
        queue = connect_queue(connection, name)
        error = ''
        try:
            queue.delete(if_empty=force)
        except Exception as err:
            error = err
        click.secho(
            f'Queue has been deleted: {queue.name} {error}',
            fg='green'
        )
