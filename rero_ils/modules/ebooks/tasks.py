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
from ..documents.api import Document, DocumentsSearch
from ..utils import do_bulk_index


@shared_task(ignore_result=True)
def create_records(records):
    """Records creation and indexing."""
    n_updated = 0
    n_created = 0
    uuids = []
    for record in records:
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
                    pid = next(query.scan()).pid
                except StopIteration:
                    pid = None

        try:
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
        except Exception as err:
            current_app.logger.error(
                'EBOOKS CREATE RECORDS: {err} {record}'.format(
                    err=err,
                    record=record
                )
            )
    do_bulk_index(uuids, doc_type='doc', process=True)

    current_app.logger.info(
        'create_records: {updated} updated, {created} new'.format(
            updated=n_updated,
            created=n_created
        )
    )
    return n_created, n_updated


@shared_task(ignore_result=True)
def delete_records(records):
    """Records deleting."""
    count = 0
    for record in records:
        # check if exist
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
        try:
            if pid:
                # update the record
                existing_record = Document.get_record_by_pid(pid)
                # TODO: delete record and linked references
                count += 1
        except Exception as err:
            current_app.logger.error(
                'EBOOKS DELETE RECORDS: {err} {record}'.format(
                    err=err,
                    record=record
                )
            )
    current_app.logger.info('delete_records: {count}'.format(
        count=count
    ))
    return count
