# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

from rero_ils.modules.documents.commons.subjects import SubjectFactory

CREATOR_ROLES = [
    'aut', 'cmp', 'cre', 'dub', 'pht', 'ape', 'aqt', 'arc', 'art', 'aus',
    'chr', 'cll', 'com', 'drt', 'dsr', 'enj', 'fmk', 'inv', 'ive', 'ivr',
    'lbt', 'lsa', 'lyr', 'pra', 'prg', 'rsp', 'scl'
]


class BaseDocumentFormatterMixin(ABC):
    """Base formatter class."""

    def __init__(self, record):
        """Initialize RIS formatter with the specific record."""
        self.record = record

    @abstractmethod
    def format(self):
        """Return formatted record."""
        raise NotImplementedError

    def _get_document_types(self) -> list[str]:
        """Return document types."""
        doc_types = []
        for main_type, subtype in [
            (doc_type.get('main_type'), doc_type.get('subtype'))
                for doc_type in self.record['type']]:
            if subtype:
                main_type = f'{main_type} / {subtype}'
            doc_types.append(main_type)

        return doc_types

    def _get_pid(self) -> str:
        """Return reference id."""
        return self.record['pid']

    def _get_title(self) -> str:
        """Return first title."""
        return next(
            filter(lambda x: x.get('type') == 'bf:Title',
                   self.record.get('title')), {}
        ).get('_text')

    def _get_secondary_title(self) -> list[str]:
        """Return secondary title."""
        # return series title if exist
        if 'seriesStatement' in self.record:
            return [
                data['value']
                for serie in self.record.get('seriesStatement', [])
                for data in serie.get('_text', [])
            ]

        # get partOf title
        return [
            part_of_title['value']
            for title in self.record.get('title', [])
            for part_of_title in title.get('partOfTitle', [])
            if 'partOf' in title['type']
        ]

    def _get_localized_contribution(self, agent) -> str:
        """Return localized contribution.

        :param agent: contribution agent data.
        :returns: Function that return localized agent based on language.
        """
        key = f'authorized_access_point_{self._language}'
        return agent.get(key)

    def _get_authors(self) -> list[str]:
        """Return authors."""

        def _extract_contribution_callback(contribution) -> str:
            """Extract value for the given contribution."""
            agent = contribution.get('agent', {})
            role = contribution.get('role', [])
            if any(r in role for r in CREATOR_ROLES):
                return self._get_localized_contribution(agent) \
                       or agent.get('preferred_name')

        return [contribution
                for contribution in map(_extract_contribution_callback,
                                        self.record.get('contribution', [])
                                        )
                if contribution]

    def _get_secondary_authors(self) -> list[str]:
        """Return other authors."""

        def _extract_contribution_callback(contribution) -> str:
            """Extract value for the given contribution."""
            agent = contribution.get('agent', {})
            role = contribution.get('role', [])
            if not any(r in role for r in CREATOR_ROLES):
                return self._get_localized_contribution(agent) \
                       or agent.get('preferred_name')

        return [contribution
                for contribution in map(_extract_contribution_callback,
                                        self.record.get('contribution', [])
                                        )
                if contribution]

    def _get_publication_year(self) -> str:
        """Return date."""
        for start_date, end_date in [
            (provision.get('startDate', ''), provision.get('endDate'))
            for provision in self.record.get('provisionActivity', [])
            if provision['type'] == 'bf:Publication'
                and any(label in provision
                        for label in ['startDate', 'endDate'])]:
            # return only the first date
            return f'{start_date} - {end_date}' if end_date else start_date

    def _get_start_pages(self) -> list[str]:
        """Return start pages."""
        return [
                   numbering['pages'].split('-')[0]
                   for part_of in self.record.get('partOf', [])
                   for numbering in part_of.get('numbering', [])
                   if 'pages' in numbering
               ] \
            or [self.record['extent']] if self.record.get('extent') else []

    def _get_end_pages(self) -> list[str]:
        """Return end pages."""
        return [
            numbering['pages'].split('-')[1]
            for part_of in self.record.get('partOf', [])
            for numbering in part_of.get('numbering', [])
            if 'pages' in numbering
               and '-' in numbering['pages']
        ]

    def _get_publication_places(self) -> list[str]:
        """Return publication places."""
        return [
            data['value']
            for provision in self.record.get('provisionActivity', [])
            for statement in provision.get('statement', [])
            for data in statement.get('label', [])
            if provision['type'] == 'bf:Publication'
            and statement['type'] == 'bf:Place'
        ]

    def _get_languages(self) -> list[str]:
        """Return languages."""
        return [lang.get('value') for lang in self.record.get('language', [])]

    def _get_publisher(self) -> list[str]:
        """Return publishers."""
        return [
            data['value']
            for provision in self.record.get('provisionActivity', [])
            for statement in provision.get('statement', [])
            for data in statement.get('label', [])
            if provision['type'] == 'bf:Publication'
            and statement['type'] == 'bf:Agent'
        ]

    def _get_isbn_or_issn(self) -> list[str]:
        """Return all isbn or issn."""
        return [
            identifier['value']
            for identifier in self.record.get('identifiedBy', [])
            if identifier['type'] in ['bf:Isbn', 'bf:Issn', 'bf:IssnL']
        ]

    def _get_electronic_locators(self) -> list[str]:
        """Return electronic locators."""
        return [
            locator['url']
            for locator in self.record.get('electronicLocator', [])
            if locator['type'] in ['resource', 'versionOfResource']
        ]

    def _get_subjects(self) -> list[str]:
        """Return keywords."""
        return [
            SubjectFactory.create_subject(subject).render(
                language=self._language)
            for subject in self.record.get('subjects', [])
        ]

    def _get_editions(self) -> list[str]:
        """Return editions."""
        return [
            edition.get('value')
            for edition_statement in self.record.get('editionStatement', [])
            for edition in edition_statement.get('_text', [])
        ]

    def _get_doi(self) -> list[str]:
        """Return list of DOI."""
        return [
            identifier['value']
            for identifier in self.record.get('identifiedBy', [])
            if identifier['type'] == 'bf:Doi'
        ]

    def _get_volume_numbers(self) -> list[str]:
        """Return volume numbers."""
        return [
            numbering['volume']
            for part_of in self.record.get('partOf', [])
            for numbering in part_of.get('numbering', [])
            if 'volume' in numbering
        ]

    def _get_issue_numbers(self) -> list[str]:
        """Return issue numbers."""
        return [
            numbering['issue']
            for part_of in self.record.get('partOf', [])
            for numbering in part_of.get('numbering', [])
            if 'issue' in numbering
        ]
