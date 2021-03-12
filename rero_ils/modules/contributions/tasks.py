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
def create_mef_record_online(ref):
    """Get a record from DB.

    If the record dos not exist get it from MEF and create it.

    :param ref: referer to contribution record on MEF
    :return: contribution pid, online = True if contribution was loaded
    """
    contribution, online = Contribution.get_record_by_ref(ref)
    pid = None
    if contribution:
        pid = contribution.get('pid')
    return pid, online
