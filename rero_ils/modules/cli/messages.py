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

"""Click command-line interface for item record management."""

import click
from flask.cli import with_appcontext

from rero_ils.modules.messages import Message


@click.group()
def messages():
    """Messages commands."""


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@messages.command()
@with_appcontext
def info():
    """Messages info."""
    click.secho(f"{'KEY':<20}{'TYPE':<15}MESSAGE", fg="green")
    for key, data in Message.get_all_messages().items():
        click.secho(f'{key:<20}{data["type"]:<15}"{data["message"]}"', fg="green")


@messages.command()
@click.argument("key")
@with_appcontext
def get(key):
    """Get messages for key."""
    if message := Message.get(key):
        click.secho(f'{key:<20}{message["type"]:<15}"{message["message"]}"', fg="green")
    else:
        click.secho(f"{key:<20}KEY NOT FOUND!", fg="red")
        raise click.BadParameter


@messages.command("set")
@click.argument("key")
@click.argument("type")
@click.argument("message")
@click.option("-t", "--timeout", "timeout", default=0)
@with_appcontext
def set_message(key, type, message, timeout):
    """Set messages for name."""
    msg = f'{key:<20}{type:<15}"{message}"'
    if Message.set(key=key, type=type, value=message, timeout=timeout):
        fg = "green"
        msg = f"OK: {msg}"
    else:
        fg = "red"
        msg = f"ERROR: {msg}"
    click.secho(msg, fg=fg)
    if fg == "red":
        raise click.BadParameter


@messages.command()
@click.argument("key")
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to delete the message?",
)
@with_appcontext
def delete(key):
    """Delete message for name."""
    if Message.delete(key=key):
        click.secho(f"{key:<20}DELETED", fg="yellow")
    else:
        click.secho(f"{key:<20}KEY NOT FOUND!", fg="red")
        raise click.BadParameter
