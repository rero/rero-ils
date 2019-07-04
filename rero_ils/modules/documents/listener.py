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

"""Signals connector for Document."""

from flask import current_app
from invenio_indexer.api import RecordIndexer
from invenio_jsonschemas import current_jsonschemas
from invenio_search import current_search
from requests import codes as requests_codes
from requests import get as requests_get

from ..documents.api import DocumentsSearch
from ..items.api import Item
from ..locations.api import Location
from ..organisations.api import Organisation


def enrich_document_data(sender, json=None, record=None, index=None,
                         **dummy_kwargs):
    """Signal sent before a record is indexed.

    :params json: The dumped record dictionary which can be modified.
    :params record: The record being indexed.
    :params index: The index in which the record will be indexed.
    :params doc_type: The doc_type for the record.
    """
    # TODO: this multiply the indexing time by 5, try an other way!
    document_index_name = DocumentsSearch.Meta.index
    if index.startswith(document_index_name):
        items = []
        available = False
        for item_pid in Item.get_items_pid_by_document_pid(record['pid']):
            item = Item.get_record_by_pid(item_pid)
            available = available or item.available
            location = Location.get_record_by_pid(
                item.replace_refs()['location']['pid']).replace_refs()
            org_pid = item.get_library().organisation_pid
            organisation = Organisation.get_record_by_pid(org_pid)
            items.append({
                'pid': item.pid,
                'barcode': item['barcode'],
                'call_number': item['call_number'],
                'status': item['status'],
                'organisation': {
                    'organisation_pid': organisation['pid'],
                    'library_pid': location['library']['pid'],
                    'organisation_library': '{}-{}'.format(
                        organisation['pid'],
                        location['library']['pid']
                    )
                }
            })
        if items:
            json['items'] = items
            json['available'] = available


def mef_person_insert(sender, *args, **kwargs):
    """Insert Signal."""
    mef_person_update_index(sender, *args, **kwargs)


def mef_person_update(sender, *args, **kwargs):
    """Update signal."""
    mef_person_update_index(sender, *args, **kwargs)


def mef_person_revert(sender, *args, **kwargs):
    """Revert signal."""
    mef_person_update_index(sender, *args, **kwargs)


def mef_person_update_index(sender, *args, **kwargs):
    """Index MEF person in ES."""
    record = kwargs['record']
    if 'documents' in record.get('$schema', ''):
        authors = record.get('authors', [])
        for author in authors:
            mef_url = author.get('$ref')
            if mef_url:
                mef_url = mef_url.replace(
                    'mef.rero.ch',
                    current_app.config['RERO_ILS_MEF_HOST']
                )
                request = requests_get(url=mef_url, params=dict(
                    resolve=1,
                    sources=1
                ))
                if request.status_code == requests_codes.ok:
                    data = request.json()
                    id = data['id']
                    data = data.get('metadata')
                    if data:
                        data['id'] = id
                        data['$schema'] = current_jsonschemas.path_to_url(
                            current_app.config[
                                'RERO_ILS_PERSONS_MEF_SCHEMA'
                            ]
                        )
                        indexer = RecordIndexer()
                        index, doc_type = indexer.record_to_index(data)
                        indexer.client.index(
                            id=id,
                            index=index,
                            doc_type=doc_type,
                            body=data,
                        )
                        current_search.flush_and_refresh(index)
                else:
                    current_app.logger.error(
                        'Mef resolver request error: {stat} {url}'.format(
                            stat=request.status_code,
                            url=mef_url
                        )
                    )
                    raise Exception('unable to resolve')


def mef_person_delete(sender, *args, **kwargs):
    """Delete signal."""
    record = kwargs['record']
    if 'documents' in record.get('$schema', ''):
        authors = record.get('authors', [])
        for author in authors:
            mef_url = author.get('$ref')
            if mef_url:
                mef_url = mef_url.replace(
                    'mef.rero.ch',
                    current_app.config['RERO_ILS_MEF_HOST']
                )
                request = requests_get(url=mef_url, params=dict(
                    resolve=1,
                    sources=1
                ))
                if request.status_code == requests_codes.ok:
                    data = request.json()
                    id = data['id']
                    data = data.get('metadata')
                    if data:
                        search = DocumentsSearch()
                        count = search.filter(
                            'match',
                            authors__pid=id
                        ).execute().hits.total
                        if count == 1:
                            indexer = RecordIndexer()
                            index, doc_type = indexer.record_to_index(data)
                            indexer.client.delete(
                                id=id,
                                index=index,
                                doc_type=doc_type
                            )
                            current_search.flush_and_refresh(index)
                else:
                    current_app.logger.error(
                        'Mef resolver request error: {result} {url}'.format(
                            result=request.status_code,
                            url=mef_url
                        )
                    )
                    raise Exception('unable to resolve')
