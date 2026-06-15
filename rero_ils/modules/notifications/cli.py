# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line interface for notifications."""

import click
from flask.cli import with_appcontext

from .models import NotificationType
from .tasks import process_notifications


@click.group()
def notifications():
    """Notification management commands."""


@notifications.command("process")
@click.option(
    "-t",
    "--type",
    "notification_type",
    help="Notification Type.",
    multiple=True,
    default=NotificationType.ALL_NOTIFICATIONS,
)
@click.option(
    "-k",
    "--enqueue",
    "enqueue",
    is_flag=True,
    default=False,
    help="Enqueue record creation.",
)
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False, help="verbose")
@with_appcontext
def process(notification_type, enqueue, verbose):
    """Process notifications."""
    results = {}
    enqueue_results = {}
    for n_type in notification_type:
        if n_type not in NotificationType.ALL_NOTIFICATIONS:
            click.secho(f"Notification type does not exist: {n_type}", fg="red")
            break
        click.secho(f"Process notification: {n_type}", fg="green")
        if enqueue:
            enqueue_results[n_type] = process_notifications.delay(notification_type=n_type, verbose=verbose)
        else:
            results[n_type] = process_notifications(notification_type=n_type, verbose=verbose)

    if verbose:
        if enqueue_results:
            for key, value in enqueue_results.items():
                results[key] = value.get()

        for key, value in results.items():
            result_values = " ".join([f"{k}={v}" for k, v in value.items()])
            click.secho(f"Notification {key:12}: {result_values}")
