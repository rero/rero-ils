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

from flask.globals import current_app

from .utils import create_contributions, title_format_text_head
from ..commons.identifiers import IdentifierFactory, IdentifierType
from ..documents.api import Document, DocumentsSearch
from ..holdings.api import HoldingsSearch
from ..items.api import ItemsSearch
from ..items.models import ItemNoteTypes
from ..local_fields.api import LocalField
from ..utils import extracted_data_from_ref
from ...utils import language_mapping


def enrich_document_data(sender, json=None, record=None, index=None,
                         doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] != DocumentsSearch.Meta.index:
        return
    holdings = []
    document_pid = record['pid']
    es_holdings = HoldingsSearch()\
        .filter('term', document__pid=document_pid)\
        .source().scan()
    for holding in es_holdings:
        holding = holding.to_dict()
        hold_data = {
            'pid': holding['pid'],
            'location': {
                'pid': holding['location']['pid'],
            },
            'circulation_category': [{
                'pid': holding['circulation_category']['pid'],
            }],
            'organisation': {
                'organisation_pid': holding['organisation']['pid'],
                'library_pid': holding['library']['pid']
            },
            'holdings_type': holding['holdings_type']
        }
        # Index additional holdings fields into the document record
        holdings_fields = [
            'call_number', 'second_call_number', 'index',
            'enumerationAndChronology', 'supplementaryContent',
            'local_fields'
        ]
        for field in holdings_fields:
            if field in holding:
                hold_data[field] = holding.get(field)
        # Index holdings notes
        if notes := [n['content'] for n in holding.get('notes', []) if n]:
            hold_data['notes'] = notes

        # Index items attached to each holdings record
        es_items = ItemsSearch()\
            .filter('term', holding__pid=holding['pid'])\
            .scan()
        for item in es_items:
            item = item.to_dict()
            item_data = {
                'pid': item['pid'],
                'barcode': item['barcode'],
                'status': item['status'],
                'local_fields': item.get('local_fields'),
                'call_number': item.get('call_number'),
                'second_call_number': item.get('second_call_number'),
                'temporary_item_type': item.get('temporary_item_type')
            }

            if 'temporary_item_type' in item:
                hold_data['circulation_category'].append(
                    {'pid': item['temporary_item_type']['pid']})

            item_data = {k: v for k, v in item_data.items() if v}

            # item acquisition part.
            #   We need to store the acquisition data of the items into the
            #   document. As we need to link acquisition date and
            #   org/lib/loc, we need to store these data together in a
            #   'nested' structure.
            if acq_date := item.get('acquisition_date'):
                item_data['acquisition'] = {
                    'organisation_pid': holding['organisation']['pid'],
                    'library_pid': holding['library']['pid'],
                    'location_pid': holding['location']['pid'],
                    'date': acq_date
                }
            # item notes content.
            #   index the content of the public notes into the document.
            public_notes_content = [
                n['content']
                for n in item.get('notes', [])
                if n['type'] in ItemNoteTypes.PUBLIC
            ]
            if public_notes_content:
                item_data['notes'] = public_notes_content
            hold_data.setdefault('items', []).append(item_data)
        holdings.append(hold_data)

    if holdings:
        json['holdings'] = holdings

    # MEF contribution ES index update
    contributions = create_contributions(json.get('contribution', []))
    if contributions:
        json.pop('contribution', None)
        json['contribution'] = contributions
    # TODO: compare record with those in DB to check which authors have
    # to be deleted from index
    # Index host document title in child document (part of)
    if 'partOf' in record:
        title = {'type': 'partOf'}
        for part_of in record['partOf']:
            doc_pid = extracted_data_from_ref(
                part_of.get('document')
            )
            document = Document.get_record_by_pid(doc_pid)
            for part_of_title in document.get('title', []):
                if 'mainTitle' in part_of_title:
                    title['partOfTitle'] = part_of_title.get(
                        'mainTitle'
                    )
        json['title'].append(title)

    # sort title
    sort_title = title_format_text_head(
        json.get('title', []),
        with_subtitle=True
    )
    language = language_mapping(json.get('language')[0].get('value'))
    if current_app.config.get('RERO_ILS_STOP_WORDS_ACTIVATE', False):
        sort_title = current_app.\
            extensions['reroils-normalizer-stop-words'].\
            normalize(sort_title, language)
    json['sort_title'] = sort_title
    # Local fields in JSON
    local_fields = LocalField.get_local_fields_by_resource(
        'doc', document_pid)
    if local_fields:
        json['local_fields'] = local_fields

    # DOCUMENT IDENTIFIERS MANAGEMENT
    #   We want to enrich document identifiers with possible alternative
    #   identifiers. For example, if document data provides an ISBN-10
    #   identifier, the corresponding ISBN-13 identifiers must be
    #   searchable too.
    identifiers = set([
        IdentifierFactory.create_identifier(identifier_data)
        for identifier_data in json.get('identifiedBy', [])
    ])
    # enrich elasticsearch data with encoded identifier alternatives. The
    # result identifiers list should contain only distinct identifier !
    for identifier in list(identifiers):
        identifiers.update(identifier.get_alternatives())
    json['identifiedBy'] = \
        [identifier.dump() for identifier in identifiers]
    # DEV NOTES :: Why copy `identifiedBy` into `nested_identifiers`
    #   We use an alternative `nested_identifiers` to duplicate identifiers
    #   into a nested structure into ES. Doing this, we can continue to search
    #   about `identifiedBy.*` using query string (nested field could not be
    #   use with query string)
    # DEV NOTES :: Why not use `copy_to` into the ES mapping.
    #   It's not possible to copy an "object" field (with properties) into a
    #   "nested" field using the `copy_to` directive ; this will cause an
    #   exception during index creation.
    #   Best solution seems to "script" this copy into the listener
    json['nested_identifiers'] = json['identifiedBy']

    # create specific keys for some common identifier families. It could
    # be used as a shortcut to search specific identifiers for expert
    # search mode.
    identifier_families = {
        'isbn': [IdentifierType.ISBN],
        'issn': [IdentifierType.ISSN, IdentifierType.L_ISSN]
    }
    for key, family_types in identifier_families.items():
        if filtered_identifiers := list(set([
            identifier.normalize()
            for identifier in identifiers
            if identifier.type in family_types
        ])):
            json[key] = filtered_identifiers

    # Populate sort date new and old for use in sorting
    pub_provisions = [
        p for p in record.get('provisionActivity', [])
        if p['type'] == 'bf:Publication'
    ]
    if pub_provisions:
        start_date = pub_provisions[0].get('startDate')
        end_date = pub_provisions[0].get('endDate')
        json['sort_date_new'] = end_date or start_date
        json['sort_date_old'] = start_date
