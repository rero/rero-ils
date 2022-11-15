# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Celery tasks to mef records."""

from __future__ import absolute_import, print_function

import click
from celery import shared_task
from flask import current_app

from .api import Contribution
from .sync import SyncAgent


@shared_task(ignore_result=True)
def delete_records(records, verbose=False):
    """Records deletion and indexing.

    :param records: records to delete
    :param verbose: verbose output
    :return: count of records
    """
    for record in records:
        status = Contribution.delete(
            record,
            force=False,
            dbcommit=True,
            delindex=True
        )
        current_app.logger.info(f'record: {record.id} | DELETED {status}')
        # TODO bulk update and reindexing
    if verbose:
        click.echo(f'records deleted: {len(records)}')
    return len(records)


@shared_task(ignore_result=True)
def sync_agents(from_last_date=True, verbose=0, dry_run=False):
    """Synchonize the agents within the MEF server.

    :param from_last_date: boolean - if True try to consider agent modified
        after the last run date time
    :param verbose: bool or integer - verbose level
    :param dry_run: bool - if true the data are not modified
    """
    agent = SyncAgent(
        from_last_date=from_last_date, verbose=verbose, dry_run=dry_run)
    n_doc_updated, n_mef_updated, sync_mef_errors = agent.sync()
    n_mef_removed, clean_mef_errors = agent.remove_unused()
    return {
        'n_doc_updated': n_doc_updated,
        'n_mef_updated': n_mef_updated,
        'clean_mef_errors': clean_mef_errors,
        'sync_mef_errors': sync_mef_errors,
        'n_mef_removed': n_mef_removed
    }
