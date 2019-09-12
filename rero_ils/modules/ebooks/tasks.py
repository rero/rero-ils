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

"""Celery tasks to create records."""

from __future__ import absolute_import, print_function

from celery import shared_task
# from celery.task.control import inspect
from flask import current_app

from .utils import create_document_holding, update_document_holding
from ..documents.api import DocumentsSearch
from ..utils import bulk_index

# from time import sleep


@shared_task(ignore_result=True)
def create_records(records):
    """Records creation and indexing."""
    n_updated = 0
    n_created = 0
    uuids = []
    for record in records:
        record['$schema'] = \
            'https://ils.rero.ch/schema/documents/document-minimal-v0.0.1.json'

        # check if already harvested
        pid = None
        for identifier in record.get('identifiedBy'):
            if identifier.get('source') == 'cantook':
                harvested_id = identifier.get('value')
                query = DocumentsSearch().filter(
                    'term',
                    identifiedBy__value=harvested_id
                ).source(includes=['pid'])
                try:
                    pid = [r.pid for r in query.scan()].pop()
                except IndexError:
                    pid = None
        if pid:
            # update the record
            record['pid'] = pid
            existing_record = update_document_holding(record, pid)
            n_updated += 1
            uuids.append(existing_record.id)
        else:
            # create a new record
            new_record = create_document_holding(record)
            if new_record:
                n_created += 1
                uuids.append(new_record.id)
    # TODO: bulk indexing does not work with travis, need to check why
    bulk_index(uuids, process=True)
    # wait for bulk index task to finish
    # inspector = inspect()
    # reserved = inspector.reserved()
    # if reserved:
    #     while any(a != [] for a in reserved.values()):
    #         reserved = inspector.reserved()
    #         sleep(1)

    current_app.logger.info('create_records: {} updated, {} new'
                            .format(n_updated, n_created))
    return n_created, n_updated
