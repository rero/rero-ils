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

"""Mixin helper class."""

from abc import ABC, abstractmethod

from flask import current_app

from rero_ils.modules.commons.identifiers import IdentifierFactory, \
    IdentifierStatus, IdentifierType
from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.utils import get_base_url

from ..api import DocumentsSearch

CREATOR_ROLES = [
    'aut', 'cmp', 'cre', 'dub', 'pht', 'ape', 'aqt', 'arc', 'art', 'aus',
    'chr', 'cll', 'com', 'drt', 'dsr', 'enj', 'fmk', 'inv', 'ive', 'ivr',
    'lbt', 'lsa', 'lyr', 'pra', 'prg', 'rsp', 'scl'
]


class BaseDocumentFormatterMixin(ABC):
    """Base formatter class."""

    # language used to localize MEF contribution
    _language = None

    def __init__(self, record, **kwargs):
        """Initialize RIS formatter with the specific record."""
        self.record = record

    @abstractmethod
    def format(self):
        """Return formatted record."""
        raise NotImplementedError

    def _get_document_types(self):
        """Return document types."""
        doc_types = []
        for main_type, subtype in [
            (doc_type.get('main_type'), doc_type.get('subtype'))
                for doc_type in self.record['type']]:
            if subtype:
                main_type = f'{main_type} / {subtype}'
            doc_types.append(main_type)

        return doc_types

    def _get_pid(self):
        """Return reference id."""
        return self.record['pid']

    def _is_masked(self):
        """Return masked information."""
        return 'Yes' if self.record.get('_masked') else 'No'

    def _get_title(self):
        """Return first title."""
        return next(
            filter(lambda x: x.get('type') == 'bf:Title',
                   self.record.get('title')), {}
        ).get('_text')

    def _get_series_statement(self):
        """Return series statement title."""
        return [
            data['value']
            for statement in self.record.get('seriesStatement', [])
            for data in statement.get('_text', [])
        ]

    def _get_secondary_title(self):
        """Return secondary title."""
        # return series title if exist
        if 'seriesStatement' in self.record:
            return self._get_series_statement()

        def _extract_part_of_title_callback(part_of):
            """Extract title for the partOf document."""
            pid = part_of.get('document', {}).get('pid')
            if es_doc := DocumentsSearch().get_record_by_pid(pid):
                title = es_doc.to_dict().get('title', [])
                return next(
                    filter(lambda x: x.get('type') == 'bf:Title',
                           title), {}
                ).get('_text')

        # get partOf title
        return [title
                for title in map(_extract_part_of_title_callback,
                                 self.record.get('partOf', []))
                if title]

    def _get_localized_contribution(self, agent):
        """Return localized contribution.

        :param agent: contribution agent data.
        :returns: Function that return localized agent based on language.
        """
        key = f'authorized_access_point_{self._language}'
        return agent.get(key)

    def _get_authors(self):
        """Return authors."""

        def _extract_contribution_callback(contribution) -> str:
            """Extract value for the given contribution."""
            agent = contribution.get('entity', {})
            role = contribution.get('role', [])
            if any(r in role for r in CREATOR_ROLES):
                return self._get_localized_contribution(agent) \
                       or agent.get('authorized_access_point')

        return [contribution
                for contribution in map(_extract_contribution_callback,
                                        self.record.get('contribution', [])
                                        )
                if contribution]

    def _get_secondary_authors(self):
        """Return other authors."""

        def _extract_contribution_callback(contribution) -> str:
            """Extract value for the given contribution."""
            agent = contribution.get('entity', {})
            role = contribution.get('role', [])
            if all(r not in role for r in CREATOR_ROLES):
                return self._get_localized_contribution(agent) \
                       or agent.get('preferred_name')

        return [contribution
                for contribution in map(_extract_contribution_callback,
                                        self.record.get('contribution', [])
                                        )
                if contribution]

    def _get_publication_year(self):
        """Return date."""
        for start_date, end_date in [
            (provision.get('startDate', ''), provision.get('endDate'))
            for provision in self.record.get('provisionActivity', [])
            if provision['type'] == 'bf:Publication'
                and any(label in provision
                        for label in ['startDate', 'endDate'])]:
            # return only the first date
            return f'{start_date} - {end_date}' if end_date else start_date

    def _get_start_pages(self):
        """Return start pages."""
        return [
           numbering['pages'].split('-')[0]
           for part_of in self.record.get('partOf', [])
           for numbering in part_of.get('numbering', [])
           if 'pages' in numbering
        ] or ([self.record['extent']] if self.record.get('extent') else [])

    def _get_end_pages(self):
        """Return end pages."""
        return [
            numbering['pages'].split('-')[1]
            for part_of in self.record.get('partOf', [])
            for numbering in part_of.get('numbering', [])
            if 'pages' in numbering
               and '-' in numbering['pages']
        ]

    def _get_publication_places(self):
        """Return publication places."""
        return [
            data['value']
            for provision in self.record.get('provisionActivity', [])
            for statement in provision.get('statement', [])
            for data in statement.get('label', [])
            if provision['type'] == 'bf:Publication'
            and statement['type'] == EntityType.PLACE
        ]

    def _get_languages(self):
        """Return languages."""
        return [lang.get('value') for lang in self.record.get('language', [])]

    def _get_publisher(self):
        """Return publishers."""
        return [
            data['value']
            for provision in self.record.get('provisionActivity', [])
            for statement in provision.get('statement', [])
            for data in statement.get('label', [])
            if provision['type'] == 'bf:Publication'
            and statement['type'] == EntityType.AGENT
        ]

    def _get_identifiers(self, types, states=None):
        """Return all identifier for the given types and states.

        :param types: list of identifier types
        :param states: list of identifier status. Default state is undefined.
        :returns: all identifiers matching arguments.
        """
        identifiers = [
            IdentifierFactory.create_identifier(identifier)
            for identifier in self.record.get('identifiedBy', [])
            if identifier['type'] in types
        ]
        states = states or [IdentifierStatus.UNDEFINED]
        return [
            identifier.normalize()
            for identifier in identifiers
            if identifier.status in states
        ]

    def _get_isbn(self, states=None):
        """Return ISBN identifiers.

        :param states: list of identifier status.
        """
        states = states or [IdentifierStatus.UNDEFINED]
        return self._get_identifiers([IdentifierType.ISBN], states)

    def _get_issn(self, states=None):
        """Return ISSN identifiers.

        :param states: list of identifier status.
        """
        return self._get_identifiers([IdentifierType.ISSN,
                                      IdentifierType.L_ISSN], states)

    def _get_doi(self):
        """Return DOI identifiers."""
        return self._get_identifiers([IdentifierType.DOI])

    def _get_electronic_locators(self):
        """Return electronic locators."""
        return [
            locator['url']
            for locator in self.record.get('electronicLocator', [])
            if locator['type'] in ['resource', 'versionOfResource']
        ]

    def _get_permalink(self):
        """Return permalink."""
        base_url = get_base_url()
        return f"{base_url}/global/documents/{self.record['pid']}"

    def _get_subjects(self):
        """Return keywords."""
        return self.record.get('subjects', [])

    def _get_editions(self):
        """Return editions."""
        return [
            edition.get('value')
            for edition_statement in self.record.get('editionStatement', [])
            for edition in edition_statement.get('_text', [])
        ]

    def _get_volume_numbers(self):
        """Return volume numbers."""
        return [
            numbering['volume']
            for part_of in self.record.get('partOf', [])
            for numbering in part_of.get('numbering', [])
            if 'volume' in numbering
        ]

    def _get_issue_numbers(self):
        """Return issue numbers."""
        return [
            numbering['issue']
            for part_of in self.record.get('partOf', [])
            for numbering in part_of.get('numbering', [])
            if 'issue' in numbering
        ]


class DocumentFormatter(BaseDocumentFormatterMixin):
    """Document formatter class."""

    def __init__(self, record, language=None, include_fields=None):
        """Initialize RIS formatter with the specific record."""
        super().__init__(record)
        self._language = language or current_app \
            .config.get('BABEL_DEFAULT_LANGUAGE', 'en')
        self._include_fields = include_fields or [
            'document_pid', 'document_type', 'document_title',
            'document_secondary_title', 'document_creator', 'document_masked',
            'document_secondary_authors', 'document_publisher',
            'document_publication_year', 'document_publication_place',
            'document_edition_statement', 'document_series_statement',
            'document_start_page', 'document_end_page', 'document_language',
            'document_isbn', 'document_issn', 'document_electronic_locator',
            'document_permalink', 'document_subjects', 'document_doi',
            'document_volume_number', 'document_issue_number',
        ]

    def format(self):
        """Return RIS export for single record."""
        return self._fetch_fields()

    @property
    def available_fields(self):
        """All available fields for document."""
        return {
            'document_pid': self._get_pid,
            'document_type': self._get_document_types,
            'document_masked': self._is_masked,
            'document_title': self._get_title,
            'document_secondary_title': self._get_secondary_title,
            'document_creator': self._get_authors,
            'document_secondary_authors': self._get_secondary_authors,
            'document_publisher': self._get_publisher,
            'document_publication_year': self._get_publication_year,
            'document_publication_place': self._get_publication_places,
            'document_edition_statement': self._get_editions,
            'document_series_statement': self._get_series_statement,
            'document_start_page': self._get_start_pages,
            'document_end_page': self._get_end_pages,
            'document_language': self._get_languages,
            'document_isbn': self._get_isbn,
            'document_issn': self._get_issn,
            'document_electronic_locator': self._get_electronic_locators,
            'document_permalink': self._get_permalink,
            'document_subjects': self._get_subjects,
            'document_doi': self._get_doi,
            'document_volume_number': self._get_volume_numbers,
            'document_issue_number': self._get_issue_numbers,
        }

    def _fetch_fields(self):
        """Return formatted output based on export fields."""
        return {
            field: self.post_process(self.available_fields[field]())
            for field in self._include_fields
        }

    def post_process(self, data):
        """Post process data."""
