# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line utilities."""

from datetime import UTC

import click
import dateparser
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_rest.utils import obj_or_import_string
from invenio_search.cli import index
from kombu import Queue

from ..api import IlsRecordsIndexer
from ..monitoring.api import Monitoring
from ..tasks import process_bulk_queue
from .utils import abort_if_false, get_record_class_from_schema_or_pid_type


def connect_queue(connection=None, name=None):
    """Queue establish connection or create queue.

    :param connection: Kombu connection to bind to. When None, returns an unbound queue.
    :param name: Name for queue, if None the INDEXER_MQ_QUEUE is used.
    :returns: connected queue.
    """
    if name:
        exchange = current_app.config.get("INDEXER_MQ_EXCHANGE")
        if connection:
            exchange = exchange(connection)
        queue = Queue(name, exchange=exchange, routing_key=name)
    else:
        queue = current_app.config["INDEXER_MQ_QUEUE"]
    return queue(connection) if connection else queue


@index.command()
@click.option("--delayed", "-d", is_flag=True, help="Run indexing in background.")
@click.option(
    "--concurrency",
    "-c",
    default=1,
    type=int,
    help="Number of concurrent indexing tasks to start.",
)
@click.option(
    "--with_stats",
    is_flag=True,
    default=False,
    help="report number of success and list failed error response.",
)
@click.option(
    "--queue",
    "-q",
    type=str,
    default=None,
    help="Name of the celery queue used to put the tasks into.",
)
@click.option("--version-type", help="search index version type to use.")
@click.option(
    "--raise-on-error/--skip-errors",
    default=True,
    help="Controls if search bulk indexing errors raise an exception.",
)
@with_appcontext
def run(delayed, concurrency, with_stats, version_type=None, queue=None, raise_on_error=True):
    """Run bulk record indexing."""
    if delayed:
        click.secho(
            f"Starting {concurrency} tasks for indexing records ({queue})...",
            fg="green",
        )
        celery_kwargs = {
            "kwargs": {
                "version_type": version_type,
                "queue": queue,
                "search_bulk_kwargs": {"raise_on_error": raise_on_error},
                "stats_only": not with_stats,
            }
        }
        for _ in range(concurrency):
            process_id = process_bulk_queue.apply_async(**celery_kwargs)
            click.secho(f"Index async ({queue}): {process_id}", fg="yellow")

    else:
        if queue:
            click.secho(f"Indexing records ({queue})...", fg="green")
        else:
            click.secho("Indexing records ...", fg="green")
        connected_queue = connect_queue(name=queue) if queue else None
        indexer = IlsRecordsIndexer(
            version_type=version_type,
            queue=connected_queue,
            routing_key=queue,
        )
        name, count = indexer.process_bulk_queue(
            search_bulk_kwargs={"raise_on_error": raise_on_error},
            stats_only=(not with_stats),
        )
        click.secho(f'"{name}" indexed: {count[0]} error: {count[1]}', fg="yellow")


@index.command()
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to reindex records?",
)
@click.option("-t", "--pid-types", multiple=True)
@click.option("-f", "--from_date", "from_date")
@click.option("-u", "--until_date", "until_date")
@click.option("-d", "--direct", "direct", is_flag=True, default=False)
@click.option("-q", "--queue", "queue", default="indexer")
@with_appcontext
def reindex(pid_types, from_date, until_date, direct, queue):
    """Reindex records.

    :param pid_type: Pid type.
    :param from_date: Index records from date.
    :param until_date: Index records until date.
    :param direct: Use record class for indexing.
    :param queue: Queue name to use.
    """
    endpoints = current_app.config.get("RECORDS_REST_ENDPOINTS")
    if not pid_types:
        pid_types = list(endpoints)
    for pid_type in pid_types:
        if pid_type in endpoints:
            msg = f"Sending {pid_type} to indexing queue "
            msg += f"({queue}): " if queue else ": "
            if direct:
                msg = f"Indexing {pid_type}: "
            click.secho(msg, fg="green", nl=False)
            query = None
            record_cls = obj_or_import_string(endpoints[pid_type].get("record_class"))
            if from_date or until_date:
                model_cls = record_cls.model_cls
                if model_cls != RecordMetadata:
                    query = (
                        model_cls.query.filter(model_cls.is_deleted.is_(False))
                        .with_entities(model_cls.id)
                        .order_by(model_cls.created)
                    )
                    if from_date:
                        dt = dateparser.parse(from_date)
                        if dt:
                            dt = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
                            query = query.filter(model_cls.updated > dt)
                    if until_date:
                        dt = dateparser.parse(until_date)
                        if dt:
                            dt = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
                            query = query.filter(model_cls.updated <= dt)
            else:
                query = (
                    PersistentIdentifier.query.filter_by(object_type="rec", status=PIDStatus.REGISTERED)
                    .filter_by(pid_type=pid_type)
                    .with_entities(PersistentIdentifier.object_uuid)
                )
            if query:
                click.echo(f"{query.count()}")
                if direct:
                    for idx, id in enumerate((x[0] for x in query), 1):
                        msg = f"{idx}\t{id}\t"
                        try:
                            rec = record_cls.get_record(id)
                            msg += f"{rec.pid}"
                            rec.reindex()
                        except Exception as err:
                            msg += f"\t{err}"
                        click.echo(msg)
                else:
                    exchange = current_app.config.get("INDEXER_MQ_EXCHANGE")
                    simple_queue = Queue(queue, exchange=exchange, routing_key=queue)
                    indxer = IlsRecordsIndexer(queue=simple_queue, routing_key=queue)
                    indxer.bulk_index((x[0] for x in query), doc_type=pid_type)
            else:
                click.echo("Cannot index by date.")
        else:
            click.secho(f"ERROR type does not exist: {pid_type}", fg="red")
        if not direct:
            msg = 'Execute "invenio reroils index run'
            if queue != "indexer":
                msg = f"{msg} -q {queue}"
            msg = f'{msg}" command to process the queue!'
            click.secho(msg, fg="yellow")


@index.command("reindex_missing")
@click.option("-t", "--pid-types", multiple=True, required=True)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False)
@with_appcontext
def reindex_missing(pid_types, verbose):
    """Index all missing records.

    :param pid_type: Pid type.
    """
    for p_type in pid_types:
        click.secho(f"Indexing missing {p_type}: ", fg="green", nl=False)
        record_class = get_record_class_from_schema_or_pid_type(pid_type=p_type)
        if not record_class:
            click.secho(
                "ERROR pid type does not exist!",
                fg="red",
            )
            continue
        monitoring = Monitoring(time_delta=0)
        pids_search, pids_db, pids_search_double, index = monitoring.get_search_db_missing_pids(p_type)
        click.secho(
            f"{len(pids_db)}",
            fg="green",
        )
        for idx, pid in enumerate(pids_db, 1):
            record = record_class.get_record_by_pid(pid)
            if record:
                record.reindex()
                if verbose:
                    click.secho(f"{idx}\t{p_type}\t{pid}")
            else:
                if verbose:
                    click.secho(f"NOT FOUND: {idx}\t{p_type}\t{pid}", fg="red")


@index.group()
def queue():
    """Manage indexing queue."""


@queue.command("init")
@click.option("-n", "--name", default=None)
@with_appcontext
def init_queue(name):
    """Initialize indexing queue.

    :papram name: Name of queue.
    """
    with current_app.extensions["invenio-celery"].celery.connection() as connection:
        queue = connect_queue(connection, name)
        result = queue.declare()
        click.secho(f"Queue has been initialized: {result}", fg="green")


@queue.command("purge")
@click.option("-n", "--name", default=None)
@with_appcontext
def purge_queue(name):
    """Purge indexing queue.

    :papram name: Name of queue.
    """
    with current_app.extensions["invenio-celery"].celery.connection() as connection:
        queue = connect_queue(connection, name)
        try:
            result = queue.purge()
        except Exception as err:
            result = err
        click.secho(f"Queue has been purged: {queue.name} {result}", fg="green")


@queue.command("delete")
@click.option("-n", "--name", default=None)
@click.option("-f", "--force", is_flag=True, default=True)
@with_appcontext
def delete_queue(name, force):
    """Delete indexing queue.

    :papram name: Name of queue.
    :papram force: Force delete the queue.
    """
    with current_app.extensions["invenio-celery"].celery.connection() as connection:
        queue = connect_queue(connection, name)
        error = ""
        try:
            queue.delete(if_empty=force)
        except Exception as err:
            error = err
        click.secho(f"Queue has been deleted: {queue.name} {error}", fg="green")
