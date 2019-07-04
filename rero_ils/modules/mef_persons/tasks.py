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

from .api import MefPerson


@shared_task(ignore_result=True)
def create_mef_records(records, verbose=False):
    """Records creation and indexing."""
    for record in records:
        rec, status = MefPerson.create_or_update(
            record,
            dbcommit=True,
            reindex=True,
            delete_pid=False
        )
        if verbose:
            click.echo(
                'record uuid: {id} | {status}'.format(id=rec.id, status=status)
            )
    return len(records)


@shared_task(ignore_result=True)
def delete_records(records, force=False, delindex=True, verbose=False):
    """Records deletion and indexing."""
    for record in records:
        status = MefPerson.delete(record, force=force, delindex=delindex)
        current_app.logger.info(
            'record: {id} | DELETED {status}'.format(
                id=record.id,
                status=status
            )
        )
        # TODO bulk update and reindexing
    if verbose:
        click.echo(
            'records deleted: {count}'.format(count=len(records))
        )
    return len(records)
