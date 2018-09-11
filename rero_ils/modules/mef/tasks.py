# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Celery tasks to mef records."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app

from .api import MefPerson


@shared_task(ignore_result=True)
def create_mef_records(records):
    """Records creation and indexing."""
    for record in records:
        rec, status = MefPerson.create_or_update(
            record,
            dbcommit=True,
            reindex=True
        )
        current_app.logger.info(
            'record uuid: {0} | {1}'.format(rec.id, status)
        )
    return len(records)


@shared_task(ignore_result=True)
def delete_records(records, force=False, delindex=True):
    """Records deletion and indexing."""
    for record in records:
        status = MefPerson.delete(record, force=force, delindex=delindex)
        current_app.logger.info(
            'record: {0} | DELETED {1}'.format(record, status)
        )
        # TODO bulk update and reindexing
    current_app.logger.info(
        'records deleted: {0}'.format(len(records))
    )
    return len(records)
