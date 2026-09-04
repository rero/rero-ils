# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line interface for operation_log record management."""

import click
from flask.cli import with_appcontext

from rero_ils.modules.operation_logs.api import OperationLog


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.command("destroy_operation_logs")
@click.option(
    "--yes-i-know",
    is_flag=True,
    callback=abort_if_false,
    expose_value=False,
    prompt="Do you really want to remove all the operation logs?",
)
@with_appcontext
def destroy_operation_logs():
    """Removes all the operation logs data."""
    OperationLog.delete_indices()
    click.secho("All operations logs have been removed", fg="green")
