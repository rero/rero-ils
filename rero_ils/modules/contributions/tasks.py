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

from .api import Contribution, ContributionUpdateAction
from ..utils import set_timestamp


@shared_task(ignore_result=True)
def create_mef_records(records, verbose=False):
    """Records creation and indexing.

    :param records: records to create
    :param verbose: verbose output
    :return: count of records
    """
    # TODO: check update an existing record
    for record in records:
        rec = Contribution.create(
            record,
            dbcommit=True,
            reindex=True,
            delete_pid=False
        )
        if verbose:
            click.echo(f'record uuid: {rec.id}')
    return len(records)


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
def update_contributions(pids=None, dbcommit=True, reindex=True, verbose=False,
                         debug=False, timestamp=True):
    """Update contributions.

    :param pids: contribution pids to update, default ALL.
    :param dbcommit: if True call dbcommit, make the change effective in db.
    :param reindex: reindex the record.
    :param verbose: verbose print.
    :param debug: debug print.
    :param timestamp: create timestamp.
    """
    pids = pids or list(Contribution.get_all_pids())
    log = {}
    error_pids = []
    if verbose:
        click.echo(f'Contribution update: {len(pids)}')
    for idx, pid in enumerate(pids, 1):
        cont = Contribution.get_record_by_pid(pid)
        msg, _ = cont.update_online(dbcommit=dbcommit, reindex=reindex,
                                    verbose=verbose)
        log.setdefault(msg, 0)
        log[msg] += 1
        if debug or (verbose and msg != ContributionUpdateAction.UPTODATE):
            click.echo(f'{idx:>10} mef:{pid:>10} {msg} {cont.source_pids()}')
        if ContributionUpdateAction.ERROR:
            error_pids.append(pid)
    if timestamp:
        set_timestamp('update_contributions', **log)
    return log, error_pids
