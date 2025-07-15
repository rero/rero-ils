# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Command line interface for migration data record management."""

import json
from random import choice

import click
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Index
from flask.cli import with_appcontext

from rero_ils.modules.utils import JsonWriter

from ..api import Migration
from .api import DeduplicationCandidate, DeduplicationStatus


@click.group()
def data():
    """Migration data commands."""


@data.command()
@click.argument("migration")
@click.argument("infile", type=click.File("r"))
@click.option("-n", "--dry-run", is_flag=True, default=False)
@with_appcontext
def load(migration, infile, dry_run):
    """Load the data for a given migration."""
    try:
        migration = Migration.get(migration)
    except NotFoundError:
        click.secho(f"Migration with: {migration} does not exists", fg="yellow")
        raise click.Abort()
    ConvertClass = migration.conversion_class
    MigrationData = migration.data_class
    with click.progressbar(ConvertClass.loads(infile)) as bar:
        for record in bar:
            if dry_run:
                pass
            else:
                migration_data = MigrationData(
                    raw=record, migration_id=migration.meta.id
                )
                migration_data.save()
    index = Index(migration.data_index_name)
    index.refresh()
    n_data = (
        MigrationData.search().filter("term", migration_id=migration.meta.id).count()
    )
    click.secho(f"Migration ({migration}) has now {n_data} converted files.")


@data.command()
@click.argument("migration")
@click.option("-i", "--id")
@click.option("-n", "--dry-run", is_flag=True, default=False)
@click.option("-f", "--force", is_flag=True, default=False)
@with_appcontext
def dedup(migration, id, dry_run, force):
    """Load the data for a given migration."""
    try:
        migration = Migration.get(migration)
    except NotFoundError:
        click.secho(f"Migration with: {migration} does not exists", fg="yellow")
        raise click.Abort()
    ConvertClass = migration.conversion_class
    MigrationData = migration.data_class
    search = MigrationData.search()
    if id:
        search = search.filter("ids", values=id.split(","))
    with click.progressbar(list(search.scan()), length=search.count()) as bar:
        for record in bar:
            ils_pid, logs, status, candidates = ConvertClass.dedup(record, force)
            if dry_run:
                for pid, json, score, detailed_score in candidates:
                    pass
            else:
                record.deduplication.candidates = [
                    DeduplicationCandidate(
                        pid=pid,
                        json=json,
                        score=score,
                        detailed_score=detailed_score,
                    )
                    for pid, json, score, detailed_score in candidates
                ]
                record.deduplication.logs = logs
                record.deduplication.status = status
                record.deduplication.ils_pid = ils_pid
                record.save()


@data.command()
@click.argument("migration")
@click.option("-i", "--id")
@click.option("-c", "--conversion-status")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["raw", "json", "markdown", "ids", "logs", "conversion-status"]),
    default="json",
)
@click.option("-o", "--out-file")
@with_appcontext
def get(migration, id, conversion_status, format, out_file):
    """Get migration data."""
    try:
        migration = Migration.get(migration)
    except NotFoundError:
        click.secho(f"Migration with: {migration} does not exists", fg="yellow")
        raise click.Abort()
    DataMigration = migration.data_class

    def format_data(data, format=json):
        """Display the data for a given format."""
        if format == "json":
            return data.conversion.to_dict().get("json")
        if format == "ids":
            return data.meta.id
        if format == "raw":
            return data.raw.decode()
        if format == "markdown":
            ConversionClass = migration.conversion_class
            return ConversionClass.markdown(data.raw)
        if format == "conversion-status" and hasattr(data.conversion, "status"):
            return (data.meta.id, data.conversion.status)
        return None

    if out_file:
        out_file = JsonWriter(out_file) if format == "json" else open(out_file, "w")
    search = DataMigration.search()
    if id:
        search = search.filter("term", _id=id)
    if conversion_status:
        search = search.filter("term", conversion__status=conversion_status)
    for data in search.scan():
        msg = format_data(data=data, format=format)
        if format == "logs":
            msg = f"Logs for {data.meta.id}"
            if out_file:
                out_file.write(f"{msg}\n")
            if hasattr(data.conversion.logs, "info"):
                msg = "\n".join(data.conversion.logs.info)
                click.secho(msg, fg="green")
            if hasattr(data.conversion.logs, "warnings"):
                msg = "\n".join(data.conversion.logs.warnings)
                click.secho(msg, fg="yellow")
            if hasattr(data.conversion.logs, "error"):
                msg = "\n".join(data.conversion.logs.error)
                click.secho(msg, fg="red")
            if out_file:
                out_file.write(f"{msg}\n")
        else:
            if format == "json":
                pass
            else:
                pass
            if out_file:
                out_file.write(msg)
                if format != "json":
                    out_file.write("\n")
    if out_file:
        out_file.close()


@data.command()
@click.argument("migration")
@click.argument("sets", type=str)
@click.option(
    "-s", "--status", type=click.Choice([item.value for item in DeduplicationStatus])
)
@with_appcontext
def subsets(migration, sets, status):
    """Get migration data."""
    try:
        migration = Migration.get(migration)
    except NotFoundError:
        click.secho(f"Migration with: {migration} does not exists", fg="yellow")
        raise click.Abort()
    DataMigration = migration.data_class
    sets = sets.split(",")

    search = DataMigration.search()
    if status:
        search = search.filter("term", deduplication__status=status)

    n = 0
    with click.progressbar(list(search.scan()), length=search.count()) as bar:
        for record in bar:
            record.deduplication.subset = choice(sets)
            record.save()
            n += 1
    click.secho(f"{n} records has been assigned to {len(sets)} sets.")
