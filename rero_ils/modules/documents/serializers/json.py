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

"""RERO Document JSON serialization."""

from flask import current_app, json, request, stream_with_context
from werkzeug.local import LocalProxy

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.utils import process_literal_contributions
from rero_ils.modules.documents.views import create_title_alternate_graphic, \
    create_title_responsibilites, create_title_variants, subject_format
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.organisations.api import OrganisationsSearch
from rero_ils.modules.serializers import JSONSerializer

from ..dumpers import document_replace_refs_dumper
from ..extensions import TitleExtension

GLOBAL_VIEW_CODE = LocalProxy(lambda: current_app.config.get(
    'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))


class DocumentJSONSerializer(JSONSerializer):
    """Serializer for RERO-ILS `Document` records as JSON."""

    @staticmethod
    def _get_view_information():
        """Get the `view_id` and `view_code` to use to build response."""
        view_id = None
        view_code = request.args.get('view', GLOBAL_VIEW_CODE)
        if view_code != GLOBAL_VIEW_CODE:
            view_id = OrganisationsSearch() \
                .get_record_by_viewcode(view_code, 'pid')['pid']
        return view_id, view_code

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        rec = record
        titles = rec.get('title', [])

        # build subjects text for display purpose
        #   Subject formatting must be done before `replace_refs` otherwise the
        #   referenced object couldn't be performed
        # TODO :: Find a way to get language to use to render subject using
        #         `Accepted-language` header.
        language = None
        for subject in record.get('subjects', []):
            subject['_text'] = subject_format(subject, language)

        # build responsibility data for display purpose
        responsibility_statement = rec.get('responsibilityStatement', [])
        responsibilities = \
            create_title_responsibilites(responsibility_statement)
        if responsibilities:
            rec['ui_responsibilities'] = responsibilities
        # build alternate graphic title data for display purpose
        altgr_titles = create_title_alternate_graphic(titles)
        if altgr_titles:
            rec['ui_title_altgr'] = altgr_titles
        altgr_titles_responsibilities = create_title_alternate_graphic(
            titles,
            responsibility_statement
        )
        if altgr_titles_responsibilities:
            rec['ui_title_altgr_responsibilities'] = \
                altgr_titles_responsibilities

        variant_titles = create_title_variants(titles)
        # build variant title data for display purpose
        if variant_titles:
            rec['ui_title_variants'] = variant_titles
        return super().preprocess_record(
            pid=pid, record=rec, links_factory=links_factory, kwargs=kwargs)

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process each hit of a search result."""
        view_id, view_code = DocumentJSONSerializer._get_view_information()
        metadata = hit.get('metadata', {})
        pid = metadata.get('pid')

        metadata['available'] = Document.is_available(pid, view_code)
        titles = metadata.get('title', [])
        if text_title := TitleExtension.format_text(
            titles, with_subtitle=False
        ):
            metadata['ui_title_text'] = text_title
        if text_title := TitleExtension.format_text(
            titles,
            responsabilities=metadata.get('responsibilityStatement', []),
            with_subtitle=False
        ):
            metadata['ui_title_text_responsibility'] = text_title

        if view_code != GLOBAL_VIEW_CODE:
            metadata['items'] = [
                item for item in metadata.get('items', [])
                if item['organisation'].get('organisation_pid') == view_id
            ]
        super()._postprocess_search_hit(hit)

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        view_id, view_code = DocumentJSONSerializer._get_view_information()

        # format the results of the facet 'year' to be displayed
        # as range
        if aggregations.get('year'):
            aggregations['year']['type'] = 'range'
            aggregations['year']['config'] = {
                'min': -9999,
                'max': 9999,
                'step': 1
            }

        if aggr_org := aggregations.get('organisation', {}).get('buckets', []):
            # For a "local view", we only need the facet on the location
            # organisation. We can filter the organisation aggregation to keep
            # only this value
            if view_code != GLOBAL_VIEW_CODE:
                aggr_org = list(
                    filter(lambda term: term['key'] == view_id, aggr_org)
                )
                aggregations['organisation']['buckets'] = aggr_org

            for org in aggr_org:
                # filter libraries by organisation
                #   Keep only libraries for the current selected organisation.
                query = LibrariesSearch() \
                    .filter('term', organisation__pid=org['key'])\
                    .source(['pid', 'name'])
                org_libraries = {hit.pid: hit.name for hit in query.scan()}
                org['library']['buckets'] = list(filter(
                    lambda lib: lib['key'] in org_libraries,
                    org['library']['buckets']
                ))
                for term in org['library']['buckets']:
                    if term['key'] in org_libraries:
                        term['name'] = org_libraries[term['key']]

                # filter locations by library
                for library in org['library']['buckets']:
                    query = LocationsSearch() \
                        .filter('term', library__pid=library['key'])\
                        .source(['pid', 'name'])
                    lib_locations = {hit.pid: hit.name for hit in query.scan()}
                    library['location']['buckets'] = list(filter(
                        lambda lib: lib['key'] in lib_locations,
                        library['location']['buckets']
                    ))
                    for term in library['location']['buckets']:
                        if term['key'] in lib_locations:
                            term['name'] = lib_locations[term['key']]

            # Complete Organisation aggregation information
            # with corresponding resource name
            JSONSerializer.enrich_bucket_with_data(
                aggr_org,
                OrganisationsSearch, 'name'
            )

            # For a "local view", we replace the organisation aggregation by
            # a library aggregation containing only for the local organisation
            if view_code != GLOBAL_VIEW_CODE:
                aggregations['library'] = aggr_org[0].get('library', {})
                del aggregations['organisation']

        super()._postprocess_search_aggregations(aggregations)


class DocumentExportJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON.

    Compared to the default JSONSerializer, this serializes only document
    metadata without any other information like aggregations, links...
    The search serialization implements stream results with context.
    """

    @staticmethod
    def _format_args():
        """Get JSON dump indentation and separates."""
        return dict(
            indent=2,
            separators=(', ', ': '),
        )

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        record = record.dumps(document_replace_refs_dumper)
        if contributions := process_literal_contributions(
                record.get('contribution', [])):
            record['contribution'] = contributions
        return json.dumps(record, **self._format_args())

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        records = [
            hit['_source']
            for hit in search_result['hits']['hits']
        ]
        return stream_with_context(json.dumps(records, **self._format_args()))
