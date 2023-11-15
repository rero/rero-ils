# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Indexing dumper."""

from flask import current_app
from invenio_records.dumpers import Dumper

from ..extensions import TitleExtension
from ..utils import process_i18n_literal_fields


class IndexerDumper(Dumper):
    """Document indexer."""

    @staticmethod
    def _process_holdings(record, data):
        """Add holding information to the indexed record."""
        from rero_ils.modules.holdings.api import HoldingsSearch
        from rero_ils.modules.items.api.api import ItemsSearch
        from rero_ils.modules.items.models import ItemNoteTypes
        holdings = []
        es_holdings = HoldingsSearch()\
            .filter('term', document__pid=record['pid'])\
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
            data['holdings'] = holdings

    @staticmethod
    def _process_identifiers(record, data):
        """Add identifiers informations for indexing."""
        from rero_ils.modules.commons.identifiers import IdentifierFactory, \
            IdentifierType

        #   Enrich document identifiers with possible alternative
        #   identifiers. For example, if document data provides an ISBN-10
        #   identifier, the corresponding ISBN-13 identifiers must be
        #   searchable too.
        identifiers = set([
            IdentifierFactory.create_identifier(identifier_data)
            for identifier_data in data.get('identifiedBy', [])
        ])
        # enrich elasticsearch data with encoded identifier alternatives. The
        # result identifiers list should contain only distinct identifier !
        for identifier in list(identifiers):
            identifiers.update(identifier.get_alternatives())
        data['identifiedBy'] = \
            [identifier.dump() for identifier in identifiers]
        # DEV NOTES :: Why copy `identifiedBy` into `nested_identifiers`
        # We use an alternative `nested_identifiers` to duplicate identifiers
        # into a nested structure into ES. Doing this we can continue to search
        # about `identifiedBy.*` using query string (nested field could not be
        # use with query string)
        # DEV NOTES :: Why not use `copy_to` into the ES mapping.
        # It's not possible to copy an "object" field (with properties) into a
        # "nested" field using the `copy_to` directive ; this will cause an
        # exception during index creation.
        # Best solution seems to "script" this copy into the listener
        data['nested_identifiers'] = data['identifiedBy']

        # create specific keys for some common identifier families. It could
        # be used as a shortcut to search specific identifiers for expert
        # search mode.
        identifier_families = {
            'isbn': [IdentifierType.ISBN],
            'issn': [IdentifierType.ISSN, IdentifierType.L_ISSN]
        }
        for key, family_types in identifier_families.items():
            if filtered_identifiers := list(
                {
                    identifier.normalize()
                    for identifier in identifiers
                    if identifier.type in family_types
                }
            ):
                data[key] = filtered_identifiers

    @staticmethod
    def _process_i18n_entities(record, data):
        """Process fields containing entities to allow i18n search."""
        # Contribution (aka. authors of the document)
        if contributions := data.pop('contribution', []):
            data['contribution'] = process_i18n_literal_fields(contributions)
        # Subject (could contain subdivisions to perform too)
        if subjects := data.pop('subjects', []):
            data['subjects'] = process_i18n_literal_fields(subjects)
        if genreForms := data.pop('genreForm', []):
            data['genreForm'] = process_i18n_literal_fields(genreForms)

    @staticmethod
    def _process_sort_title(record, data):
        """Compute and store the document title used to sort it."""
        from rero_ils.utils import language_mapping
        sort_title = TitleExtension.format_text(data.get('title', []))
        language = language_mapping(data.get('language')[0].get('value'))
        if current_app.config.get('RERO_ILS_STOP_WORDS_ACTIVATE', False):
            sort_title = current_app. \
                extensions['reroils-normalizer-stop-words']. \
                normalize(sort_title, language)
        data['sort_title'] = sort_title

    @staticmethod
    def _process_local_field(record, data):
        """Add local field data related to this document."""
        from rero_ils.modules.local_fields.api import LocalField
        data['local_fields'] = [{
            'organisation_pid': field.organisation_pid,
            'fields': field.get('fields')
        } for field in LocalField.get_local_fields_by_id('doc', record['pid'])]
        if not data['local_fields']:
            del data['local_fields']

    @staticmethod
    def _process_host_document(record, data):
        """Store host document title in child document (part of)."""
        from ..api import Document
        for part_of in data.get('partOf', []):
            doc_pid = part_of.get('document', {}).get('pid')
            document = Document.get_record_by_pid(doc_pid).dumps()
            if titles := [
                v['_text']
                for v in document.get('title', {})
                if v.get('_text') and v.get('type') == 'bf:Title'
            ]:
                part_of['document']['title'] = titles.pop()

    @staticmethod
    def _process_provision_activity(record, data):
        """Search into `provisionActivity` field to found sort dates."""
        if pub_provisions := [
            provision
            for provision in record.get('provisionActivity', [])
            if provision['type'] == 'bf:Publication'
        ]:
            start_date = pub_provisions[0].get('startDate')
            end_date = pub_provisions[0].get('endDate')
            data['sort_date_new'] = end_date or start_date
            data['sort_date_old'] = start_date

    def dump(self, record, data):
        """Dump a document instance with basic document information's.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        self._process_holdings(record, data)
        self._process_i18n_entities(record, data)
        self._process_identifiers(record, data)
        self._process_local_field(record, data)
        self._process_sort_title(record, data)
        self._process_host_document(record, data)
        self._process_provision_activity(record, data)
        # import pytz
        # from datetime import datetime
        # iso_now = pytz.utc.localize(datetime.utcnow()).isoformat()
        # for date_field in ['_created', '_updated']:
        #     if not data.get(date_field):
        #         data[date_field] = iso_now

        # TODO: compare record with those in DB to check which authors have
        #       to be deleted from index
        return data
