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

from pprint import pprint

import click
from elasticsearch.exceptions import NotFoundError
from flask.cli import with_appcontext

from ..api import Migration


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
                print(ConvertClass.markdown(record), "\n")
            else:
                MigrationData(raw=record, migration_id=migration.meta.id).save()
    n_data = (
        MigrationData.search().filter("term", migration_id=migration.meta.id).count()
    )
    click.secho(f"Migration ({migration}) has now {n_data} converted files.")


@data.command()
@click.argument("migration")
@click.option("-i", "--id")
@click.option("-s", "--status")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["raw", "json", "markdown", "ids", "logs", "status"]),
    default="json",
)
@with_appcontext
def get(migration, id, status, format):
    """Get migration data."""
    try:
        migration = Migration.get(migration)
    except NotFoundError:
        click.secho(f"Migration with: {migration} does not exists", fg="yellow")
        raise click.Abort()
    DataMigration = migration.data_class

    def display(data):
        """Display the data for a given format."""
        if format == "raw":
            print(data.raw.decode())
        if format == "json":
            pprint(data.json.to_dict())
        if format == "markdown":
            ConversionClass = migration.conversion_class
            print(ConversionClass.markdown(data.raw))
        if format == "status" and data.conversion_status:
            print(data.meta.id, data.conversion_status)
        if format == "logs" and data.conversion_logs:
            print(f"Logs for {data.meta.id}")
            if data.conversion_logs.info:
                click.secho("\n".join(data.conversion_logs.info), fg="green")
            if data.conversion_logs.warning:
                click.secho("\n".join(data.conversion_logs.warning), fg="yellow")
            if data.conversion_logs.error:
                click.secho("\n".join(data.conversion_logs.error), fg="red")

    if id:

        if format == "ids":
            pprint([id])
        else:
            display(DataMigration.get(id))
    else:
        search = DataMigration.search()
        if status:
            search = search.filter("term", conversion_status=status)
        if format == "ids":
            search = search.source()
        for data in search.scan():
            if format == "ids":
                print(data.meta.id)
            else:
                display(data)
