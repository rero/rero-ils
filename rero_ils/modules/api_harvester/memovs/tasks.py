# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ApiHarvester tasks."""

import click
from celery import shared_task

from rero_ils.modules.utils import get_timestamp, set_timestamp

from .api import ApiMemovs


@shared_task(ignore_result=True, soft_time_limit=7200)
def delete_memovs(verbose=False):
    """Delete RERO-ILS documents that have disappeared from the Memovs API.

    Fetches the full catalogue from the Memovs API, compares it against harvested documents in RERO-ILS,
    and deletes any that are no longer present remotely. Items are deleted before the document;
    holdings and local fields are cascade-deleted automatically.

    :param verbose: print progress messages to stdout.
    :returns: tuple of (deleted_count, can_not_delete_count).
    """
    name = "VS-MEMO"
    harvester = ApiMemovs(name=name, verbose=verbose)
    deleted, can_not_delete = harvester.delete_orphan_records()

    msg = f"delete_memovs {name}: deleted={deleted} can_not_delete={can_not_delete}"
    if verbose:
        click.echo(msg)

    timestamp_data = get_timestamp("api_harvester") or {}
    timestamp_data.setdefault(name, {})["delete"] = deleted
    set_timestamp("api_harvester", **timestamp_data)
    return deleted, can_not_delete
