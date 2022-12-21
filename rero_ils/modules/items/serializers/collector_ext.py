# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Item collector."""

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.utils import title_format_text_head
from rero_ils.modules.documents.views import work_access_point

from .collector import Collector


class CollectorExt(Collector):
    """collect data for csv."""

    # define chunk size
    chunk_size = 1000
    separator = ' | '

    @classmethod
    def get_documents_by_item_pids(cls, item_pids, language):
        """Get documents for the given item pid list.

        :param item_pids: item pids.
        :param language: language.
        :return list of documents.
        """

        def _build_doc(data):
            document_data = {}
            title = title_format_text_head(
                data.get('title', []), with_subtitle=True)
            document_data['document_title'] = title
            # process contributions
            creator = []
            for contribution in data.get('contribution', []):
                authorized_access_point = \
                    f'authorized_access_point_{language}'
                if authorized_access_point in contribution.get('agent'):
                    creator.append(
                        f'{contribution["agent"][authorized_access_point]}'
                        f', {contribution.get("role")}'
                    )
            document_data['document_contribution'] = ' ; '.join(creator)
            document_main_type = []
            document_sub_type = []
            for document_type in data.get('type'):
                document_main_type.append(
                    document_type.get('main_type'))
                document_sub_type.append(
                    document_type.get('subtype', ''))
            document_data['document_main_type'] = ', '.join(
                document_main_type)
            document_data['document_sub_type'] = ', '.join(
                document_sub_type)
            # masked
            document_data['document_masked'] = \
                'Yes' if data.get('_masked') else 'No'
            # isbn:
            document_data['document_isbn'] = cls.separator.join(
                data.get('isbn', []))
            # issn:
            document_data['document_issn'] = cls.separator.join(
                data.get('issn', []))
            # document_identifiedBy
            identifiers = []
            for identified_by in data.get('identifiedBy', []):
                identified_type = identified_by.get("type")
                if identified_type not in ['bf:Isbn', 'bf:Issn']:
                    identified = (
                        f'({identified_type}){identified_by.get("value")}')
                    for additional in [
                            "source", "status", "qualifier", "note"]:
                        if more := identified_by.get(additional):
                            identified = f'{identified}; {additional}: {more}'
                    identifiers.append(identified)
            document_data['document_identifiedBy'] = cls.separator.join(
                identifiers)
            # document_series_statement
            document_data['document_series_statement'] = cls.separator.join(
                data['value']
                for serie in data.get('seriesStatement', [])
                for data in serie.get('_text', [])
            )
            # document_edition_statement
            document_data['document_edition_statement'] = cls.separator.join(
                edition.get('value')
                for edition_statement in
                data.get('editionStatement', [])
                for edition in edition_statement.get('_text', [])
            )
            # process provision activity

            # we only use the first provision activity of type
            # bf:publication
            if any(
                (provision_activity := prov).get('type' == 'bf:Publication')
                for prov in data.get('provisionActivity', [])
            ):
                start_date = provision_activity.get('startDate', '')
                end_date = provision_activity.get('endDate')
                document_data['document_publication_year'] = \
                    f'{start_date} - {end_date}' \
                    if end_date else start_date

                document_data['document_publisher'] = cls.separator.join(
                    data['value']
                    for stmt in provision_activity.get('statement', [])
                    for data in stmt.get('label', [])
                    if stmt['type'] == 'bf:Agent'
                )
            # document_provisionActivity
            provision_activities = []
            for provision_activity in data.get('provisionActivity', []):
                text = provision_activity.get('_text')[0]['value']
                pa_type = provision_activity.get('type')
                provision_activities.append(f'({pa_type}){text}')
            document_data['document_provisionActivity'] = \
                cls.separator.join(provision_activities)

            # document_responsabilityStatement
            document_data['document_responsabilityStatement'] = \
                cls.separator.join(data.get('responsabilityStatement', []))
            # document_extent
            document_data['document_extent'] = data.get('extent')
            # document_tableOfContents
            document_data['document_tableOfContents'] = cls.separator.join(
                data.get('tableOfContents', []))
            # document_notes
            document_data['document_notes'] = cls.separator.join(
                    [f'{note["noteType"]}: {note["label"]}'
                    for note in data.get('note', [])])
            # document_credits
            document_data['document_credits'] = cls.separator.join(
                data.get('credits', []))
            # document_language
            languages = []
            for lang_data in data.get('language', []):
                lang_info = lang_data['value']
                if note := lang_data.get('note'):
                    lang_info = f'{lang_info}: {note}'
                languages.append(lang_info)
            document_data['document_language'] = cls.separator.join(languages)
            # document_work_access_point
            document_data['document_work_access_point'] = cls.separator.join(
                work_access_point(data.get('work_access_point', [])))
            # document_contentMediaCarrier
            content_media_carriers = []
            for content_media_carrier in data.get('contentMediaCarrier', []):
                cmc_data = []
                for cmc_type in ['contentType', 'mediaType', 'carrierType']:
                    if value := content_media_carrier.get(cmc_type):
                        if isinstance(value, list):
                            cmc_data.append(', '.join(value))
                        else:
                            cmc_data.append(value)
                content_media_carriers.append('; '.join(cmc_data))
            document_data['document_contentMediaCarrier'] = \
                cls.separator.join(content_media_carriers)

            return document_data

        doc_search = DocumentsSearch() \
            .filter('terms', holdings__items__pid=list(item_pids))
        docs = {}
        for doc in doc_search.scan():
            docs[doc.pid] = _build_doc(doc.to_dict())
        return docs

