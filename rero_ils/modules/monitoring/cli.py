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

"""Monitoring utilities."""

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_cache import current_cache
from invenio_db import db
from invenio_search import current_search_client
from redis import Redis

from .api import Monitoring, db_connection_counts_query, db_connections_query


@click.group()
def monitoring():
    """Monitoring commands."""


@monitoring.command('es_db_counts')
@click.option('-m', '--missing', 'missing', is_flag=True, default=False,
              help='Display missing pids.')
@click.option('-d', '--delay', 'delay', default=1,
              help='Get ES and DB counts from delay min minutes in the past.')
@with_appcontext
def es_db_counts_cli(missing, delay):
    """Print ES and DB counts.

    Prints a table representation of database and elasticsearch counts.
    Columns:
    1. database count minus elasticsearch count
    2. document type
    3. database count
    4. elasticsearch index
    5. elasticsearch count
    """
    missing_doc_types = []
    mon = Monitoring(time_delta=delay)
    msg_head = f'DB - ES{"type":>8}{"count":>11}{"index":>27}{"count":>11}\n'
    msg_head += f'{"":-^64s}'
    click.echo(msg_head)
    info = mon.info(with_deleted=False, difference_db_es=False)
    for doc_type in sorted(info):
        db_es = info[doc_type].get('db-es', '')
        msg = f'{db_es:>7}{doc_type:>8}{info[doc_type].get("db", ""):>11}'
        index = info[doc_type].get('index', '')
        if index:
            msg += f'{index:>27}{info[doc_type].get("es", ""):>11}'
        if db_es not in [0, '']:
            click.secho(msg, fg='red')
        else:
            click.echo(msg)
        if missing and index:
            missing_doc_types.append(doc_type)
    for missing_doc_type in missing_doc_types:
        mon.print_missing(missing_doc_type)


@monitoring.command('es_db_missing')
@click.argument('doc_type')
@click.option('-d', '--delay', 'delay', default=1,
              help='Get ES and DB counts from delay minutes in the past.')
@with_appcontext
def es_db_missing_cli(doc_type, delay):
    """Print missing pids informations."""
    mon = Monitoring(time_delta=delay)
    mon.print_missing(doc_type)


@monitoring.command('time_stamps')
@with_appcontext
def time_stamps_cli():
    """Print time_stamps information."""
    if cache := current_cache.get('timestamps'):
        for key, value in cache.items():
            time = value.pop('time')
            args = [f'{k}={v}' for k, v in value.items()]
            click.echo(f'{time}: {key} {" | ".join(args)}')


@monitoring.command('es')
@with_appcontext
def es():
    """Displays Elasticsearch cluster info."""
    for key, value in current_search_client.cluster.health().items():
        click.echo(f'{key:<33}: {value}')


@monitoring.command('es_indices')
@with_appcontext
def es_indices():
    """Displays Elasticsearch indices info."""
    click.echo(current_search_client.cat.indices(s='index'))


@monitoring.command()
@with_appcontext
def redis():
    """Displays redis info."""
    url = current_app.config.get('ACCOUNTS_SESSION_REDIS_URL',
                                 'redis://localhost:6379')
    redis = Redis.from_url(url)
    for key, value in redis.info().items():
        click.echo(f'{key:<33}: {value}')


@monitoring.command('db_connection_counts')
@with_appcontext
def db_connection_counts():
    """Display DB connection counts."""
    try:
        max_conn, used, res_for_super, free = db.session.execute(
            db_connection_counts_query).first()
    except Exception as error:
        click.secho(f'ERROR: {error}', fg='red')
    return click.secho(f'max: {max_conn}, used: {used}, '
                       f'res_super: {res_for_super}, free: {free}')


@monitoring.command('db_connections')
@with_appcontext
def db_connections():
    """Display DB connections."""
    try:
        results = db.session.execute(db_connections_query).fetchall()
    except Exception as error:
        click.secho(f'ERROR: {error}', fg='red')
    for pid, application_name, client_addr, client_port, backend_start, \
            xact_start, query_start, wait_event, state, left in results:
        click.secho(
            f'application_name: {application_name}\n'
            f'client_addr: {client_addr}\n'
            f'client_port: {client_port}\n'
            f'backend_start: {backend_start}\n'
            f'xact_start: {xact_start}\n'
            f'query_start: {query_start}\n'
            f'wait_event: {wait_event}\n'
            f'state: {state}\n'
            f'left: {left}\n'
        )
