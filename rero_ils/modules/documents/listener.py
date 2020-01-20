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

from ..documents.api import DocumentsSearch
from ..holdings.api import Holding, HoldingsSearch
from ..items.api import ItemsSearch
from ..persons.api import Person


def enrich_document_data(sender, json=None, record=None, index=None,
                         doc_type=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index == '-'.join([DocumentsSearch.Meta.index, doc_type]):
        # HOLDINGS
        holdings = []
        document_pid = record['pid']
        es_holdings = HoldingsSearch().filter(
            'term', document__pid=document_pid
        ).scan()
        for holding in es_holdings:
            data = {
                'pid': holding.pid,
                # 'available': holding.available,
                'location': {
                    'pid': holding['location']['pid'],
                },
                'circulation_category': {
                    'pid': holding['circulation_category']['pid'],
                },
                'organisation': {
                    'organisation_pid': holding['organisation']['pid'],
                    'library_pid': holding['library']['pid'],
                    'organisation_library': '{}-{}'.format(
                        holding['organisation']['pid'],
                        holding['library']['pid']
                    )
                }
            }
            # replace this by an ES query
            es_items = list(ItemsSearch().filter(
                'term', holding__pid=holding.pid
            ).scan())
            for item in es_items:
                data.setdefault('items', []).append({
                    'pid': item.pid,
                    'barcode': item.barcode,
                    'call_number': item.call_number,
                    'status': item.status,
                    'available': item.available
                })
            data['available'] = Holding.isAvailable(es_items)

            holdings.append(data)

        if holdings:
            json['holdings'] = holdings

        # MEF person ES index update
        authors = []
        for author in json.get('authors', []):
            pid = author.get('pid', None)
            if pid:
                # Check presence in DB
                author_rec = Person.get_record_by_mef_pid(pid)
                authors.append(author_rec.dumps_for_document())
            else:
                authors.append(author)
        # Put authors in JSON
        json['authors'] = authors
        # TODO: compare record with those in DB to check which authors have
        # to be deleted from index
