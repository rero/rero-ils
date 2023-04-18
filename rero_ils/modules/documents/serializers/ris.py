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

"""RIS Document serialization."""

from flask import current_app, request, stream_with_context
from invenio_i18n.ext import current_i18n
from invenio_records_rest.serializers.base import SerializerMixinInterface

from rero_ils.modules.commons.identifiers import IdentifierFactory, \
    IdentifierType
from rero_ils.utils import get_i18n_supported_languages

from .base import BaseDocumentFormatterMixin
from ..dumpers import document_replace_refs_dumper
from ..utils import process_i18n_literal_fields


class RISSerializer(SerializerMixinInterface):
    """BibTeX serializer for records."""

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        record = record.dumps(document_replace_refs_dumper)
        if contributions := record.pop('contribution', []):
            record['contribution'] = process_i18n_literal_fields(contributions)
        # enrich record data with encoded identifier alternatives. The
        # record identifiers list should contain only distinct identifier !
        identifiers = set([
            IdentifierFactory.create_identifier(identifier_data)
            for identifier_data in record.get('identifiedBy', [])
        ])

        for identifier in list(identifiers):
            identifiers.update(identifier.get_alternatives())
        record['identifiedBy'] = \
            [identifier.dump() for identifier in identifiers]
        return RISFormatter(record=record).format()

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        def generate_export():
            for hit in search_result['hits']['hits']:
                yield RISFormatter(record=hit['_source']).format()
        return stream_with_context(generate_export())


class RISFormatter(BaseDocumentFormatterMixin):
    """RIS formatter class."""

    # RIS separator between key and value
    separator = '  - '

    def __init__(self, record, doctype_mapping=None, export_fields=None):
        """Initialize RIS formatter with the specific record."""
        super().__init__(record)
        config = current_app.config \
            .get('RERO_ILS_EXPORT_MAPPER').get('ris', {})
        language = request.args.get("lang", current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')
        self._language = language
        self._doctype_mapping = doctype_mapping \
            or config.get('doctype_mapping')
        self._export_fields = export_fields or config.get('export_fields')

    def format(self):
        """Return RIS export for single record."""
        return self._fetch_fields() + f'ER{self.separator}\n'

    def _doctype_mapper(self, main_type: str, sub_type: str = None):
        """Document type mapper.

        :param: main_type: main document type.
        :param: sub_type: subtype of main document type.
        :return: mapped RIS reference type.
        """
        for ris_doc_type, func in self._doctype_mapping.items():
            if func(main_type, sub_type):
                return ris_doc_type
        return 'GEN'

    def _get_document_types(self):
        """Return document types."""
        if 'type' not in self.record:
            return ['GEN']

        return [
            self._doctype_mapper(doc_type.get('main_type'),
                                 doc_type.get('subtype'))
            for doc_type in self.record['type']
        ]

    def _get_city(self):
        """Return publication place."""
        return self._get_publication_places()

    def _get_date(self):
        return self._get_publication_year()

    def _get_primary_year(self):
        """Return primary year."""
        return self._get_publication_year()

    def _fetch_fields(self):
        """Return formatted output based on export fields."""
        available_fields = {
            'TY': self._get_document_types(),
            'ID': self._get_pid(),
            'TI': self._get_title(),
            'T2': self._get_secondary_title(),
            'AU': self._get_authors(),
            'A2': self._get_secondary_authors(),
            'DA': self._get_publication_year(),
            'ET': self._get_editions(),
            'SP': self._get_start_pages(),
            'EP': self._get_end_pages(),
            'CY': self._get_publication_places(),
            'LA': self._get_languages(),
            'PB': self._get_publisher(),
            'SN': self._get_identifiers([IdentifierType.ISBN,
                                         IdentifierType.ISSN,
                                         IdentifierType.L_ISSN]),
            'UR': self._get_electronic_locators(),
            'UR': self._get_permalink(),
            'KW': self._get_subjects(),
            'DO': self._get_identifiers([IdentifierType.DOI]),
            'VL': self._get_volume_numbers(),
            'IS': self._get_issue_numbers(),
            'PP': self._get_publication_places(),
            'Y1': self._get_publication_year(),
            'PY': self._get_publication_year()
        }
        out = ''
        for field in self._export_fields:
            if value := available_fields[field]:
                out += self._format_output_row(field, value)
        return out

    def _format_output_row(self, field, value):
        """Format output.

        :param field: RIS tag
        :param value: value for RIS tag
        :returns formatted row string
        """
        out = ''
        if isinstance(value, list):
            for v in value:
                out += f'{field}{self.separator}{v}\n'
        else:
            out += f'{field}{self.separator}{value}\n'
        return out
