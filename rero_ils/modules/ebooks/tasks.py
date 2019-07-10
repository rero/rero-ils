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

"""Celery tasks to create records."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app

from ..documents.api import Document, DocumentsSearch


@shared_task(ignore_result=True)
def create_records(records):
    """Records creation and indexing."""
    n_updated = 0
    n_created = 0
    for record in records:
        record['$schema'] = \
            'https://ils.rero.ch/schema/documents/document-minimal-v0.0.1.json'

        # check if already harvested
        harvestedID = record.get('identifiers').get('harvestedID')
        query = DocumentsSearch().filter(
            'term',
            identifiers__harvestedID=harvestedID
        ).source(includes=['pid'])

        # update the record
        try:
            pid = [r.pid for r in query.scan()].pop()
            existing_record = Document.get_record_by_pid(pid)
            existing_record.clear()
            existing_record['pid'] = pid
            existing_record.update(
                record,
                dbcommit=True,
                reindex=True)
            n_updated += 1
        # create a new record
        except IndexError:
            Document.create(
                record,
                dbcommit=True,
                reindex=True
            )
            n_created += 1
    current_app.logger.info('create_records: {} updated, {} new'
                            .format(n_updated, n_created))
