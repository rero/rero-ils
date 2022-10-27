# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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
from flask import current_app

from .utils import create_document_holding, update_document_holding
from ..documents.api import Document, DocumentsSearch
from ..utils import do_bulk_index, get_schema_for_resource, set_timestamp


@shared_task(ignore_result=True)
def create_records(records):
    """Records creation and indexing."""
    n_updated = 0
    n_created = 0
    uuids = []
    for record in records:
        # add document type
        record['type'] = [{
            'main_type': 'docmaintype_book',
            'subtype': 'docsubtype_e-book'
        }]
        # check if already harvested
        pid = None
        for identifier in record.get('identifiedBy'):
            if identifier.get('source') == 'cantook':
                harvested_id = identifier.get('value')
                query = DocumentsSearch()\
                    .filter('term', identifiedBy__value__raw=harvested_id)\
                    .source(includes=['pid'])
                try:
                    pid = next(query.scan()).pid
                except StopIteration:
                    pid = None
        try:
            # add documents schema
            pid_type = Document.provider.pid_type
            record['$schema'] = get_schema_for_resource(pid_type)
            if pid:
                # update the record
                record['pid'] = pid
                existing_record = update_document_holding(record, pid)
                n_updated += 1
                uuids.append(existing_record.id)
            elif new_record := create_document_holding(record):
                n_created += 1
                uuids.append(new_record.id)
        except Exception as err:
            current_app.logger.error(f'EBOOKS CREATE RECORDS: {err} {record}')
    do_bulk_index(uuids, doc_type='doc', process=True)

    current_app.logger.info(
        f'create_records: {n_updated} updated, {n_created} new'
    )
    set_timestamp('ebooks_create_records', created=n_created,
                  updated=n_updated)
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
                query = DocumentsSearch()\
                    .filter('term', identifiedBy__value__raw=harvested_id)\
                    .source(includes=['pid'])
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
            current_app.logger.error(f'EBOOKS DELETE RECORDS: {err} {record}')
    current_app.logger.info(f'delete_records: {count}')
    set_timestamp('ebooks_delete_records', deleted=count)
    return count
