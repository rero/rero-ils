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

"""Command line interface for migration record management."""

import contextlib

import click
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Index
from flask.cli import with_appcontext

from rero_ils.modules.migrations.api import Migration, MigrationStatus
from rero_ils.modules.utils import draw_data_table


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.group()
def migrations():
    """Migration commands."""


@migrations.group()
def index():
    """Migration indices commands."""


@index.command()
@with_appcontext
def init():
    """Initialize the migration elasticsearch index."""
    Migration.init()
    click.echo("Elasticsearch Index created.")


@index.command()
@with_appcontext
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to remove all migration data?",
)
def destroy():
    """Remove the migration elasticsearch index."""
    Index(Migration.Index.name).delete()
    click.echo("Migration Elasticsearch Index has been deleted.")


@migrations.command()
@click.argument("name")
@click.argument("library_pid")
@click.option(
    "-s", "--status", type=click.Choice([item.value for item in MigrationStatus])
)
@click.option("-d", "--description", "description", is_flag=False, default="")
@with_appcontext
def create(name, library_pid, status, description):
    """Create a given migration."""
    with contextlib.suppress(NotFoundError):
        if Migration.get(name):
            click.secho(f"Migration with name: {name} already exists.", fg="red")
            raise click.Abort()
    data = {"name": name, "library_pid": library_pid, "status": "created"}
    if description:
        data["description"] = description
    if status:
        data["status"] = status
    migration = Migration(meta={"id": name}, **data)
    try:
        migration.save()
        click.secho(
            f"ADD name: {migration.name} library: {migration.library_pid} "
            f'description:"{description}"',
            fg="green",
        )
    except Exception as err:
        click.secho(
            f"ERROR EXCEPTION: name: {name} library: {library_pid} {err}", fg="red"
        )


@migrations.command()
@click.argument("name")
@click.option(
    "-s", "--status", type=click.Choice([item.value for item in MigrationStatus])
)
@click.option("-l", "--library-pid")
@click.option("-d", "--description", is_flag=False, default="")
@with_appcontext
def update(name, status, library_pid, description):
    """Update the migration data."""
    try:
        migration = Migration.get(name)
    except NotFoundError:
        click.secho(f"Migration with: {name} does not exists", fg="yellow")
        raise click.Abort()
    if migration:
        if description:
            migration.description = description
        if status:
            migration.status = status
        if library_pid:
            migration.library_pid = library_pid
    try:
        migration.save()
        click.secho(f"Migration with name {name} has been updated.", fg="green")
    except Exception as err:
        click.secho(
            f"ERROR EXCEPTION: name: {name} library: {library_pid} {err}", fg="red"
        )


@migrations.command()
@with_appcontext
@click.option("-n", "--name")
def get(name=None):
    """Get existing migrations."""
    header = (
        ("id", 20),
        ("name", 20),
        ("Lib. Pid", 10),
        ("status", 10),
        ("description", 30),
    )
    if name:
        try:
            hits = [Migration.get(id=name)]
        except NotFoundError:
            click.secho(f"Migration with: {name} does not exists", fg="yellow")
            raise click.Abort()
    else:
        query = Migration.search()
        if query.count():
            hits = query.scan()
        else:
            click.secho(f"No migration found.", fg="yellow")
            raise click.Abort()
    click.secho(
        draw_data_table(
            header,
            [
                (
                    hit.meta.id,
                    hit.name,
                    hit.library_pid,
                    hit.status,
                    hit.description if hit.description else "",
                )
                for hit in hits
            ],
        ),
        fg="green",
    )


@migrations.command()
@click.argument("name")
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you know that you are going to destroy the migration?",
)
@with_appcontext
def delete(name):
    """Delete a given migration."""
    try:
        Migration.get(id=name).delete()
        click.secho(f"Deleted: {name}", fg="green")
    except NotFoundError:
        click.secho(f"Migration with: {name} does not exists", fg="yellow")
