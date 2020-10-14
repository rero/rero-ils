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

from .utils import create_authorized_access_point
from ..documents.api import Document, DocumentsSearch
from ..holdings.api import Holding, HoldingsSearch
from ..items.api import ItemsSearch
from ..items.models import ItemNoteTypes
from ..persons.api import Person
from ..utils import extracted_data_from_ref
from ...utils import get_i18n_supported_languages


def enrich_document_data(sender, json=None, record=None, index=None,
                         doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == DocumentsSearch.Meta.index:
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
                    'library_pid': holding['library']['pid']
                }
            }
            # items linked to the holding
            es_items = list(
                ItemsSearch().filter('term', holding__pid=holding.pid).scan()
            )
            for item in es_items:
                item_record = {
                    'pid': item.pid,
                    'barcode': item.barcode,
                    'status': item.status,
                    'available': item.available
                }
                call_number = item.to_dict().get('call_number')
                if call_number:
                    item_record['call_number'] = call_number
                # item acquisition part.
                #   We need to store the acquisition data of the items into the
                #   document. As we need to link acquisition date and
                #   org/lib/loc, we need to store theses data together in a
                #   'nested' structure.
                acq_date = item.to_dict().get('acquisition_date')
                if acq_date:
                    item_record['acquisition'] = {
                        'organisation_pid': holding['organisation']['pid'],
                        'library_pid': holding['library']['pid'],
                        'location_pid': holding['location']['pid'],
                        'date': acq_date
                    }
                # item notes content.
                #   index the content of the public notes into the document.
                public_notes_content = [
                    n['content']
                    for n in item.to_dict().get('notes', [])
                    if n['type'] in ItemNoteTypes.PUBLIC
                ]
                if public_notes_content:
                    item_record['notes'] = public_notes_content

                data.setdefault('items', []).append(item_record)
            data['available'] = Holding.isAvailable(es_items)
            holdings.append(data)

        if holdings:
            json['holdings'] = holdings

        # MEF person ES index update
        contributions = []
        for contribution in json.get('contribution', []):
            pid = contribution['agent'].get('pid')
            if pid:
                person = Person.get_record_by_pid(pid)
                if person:
                    contribution['agent'] = person.dumps_for_document()
            else:
                authorized_access_point = create_authorized_access_point(
                    contribution['agent']
                )
                for language in get_i18n_supported_languages():
                    contribution['agent'][
                        'authorized_access_point_{language}'.format(
                            language=language
                        )
                    ] = authorized_access_point
            contributions.append(contribution)
        # Put contribution in JSON
        json['contribution'] = contributions
        # TODO: compare record with those in DB to check which authors have
        # to be deleted from index
        # Index host document title in child document (part of)
        if 'partOf' in record:
            title = {'type': 'partOf'}
            for part_of in record['partOf']:
                document_pid = extracted_data_from_ref(
                    part_of.get('document')
                )
                document = Document.get_record_by_pid(document_pid)
                for part_of_title in document.get('title', []):
                    if 'mainTitle' in part_of_title:
                        title['partOfTitle'] = part_of_title.get(
                            'mainTitle'
                        )
            json['title'].append(title)
