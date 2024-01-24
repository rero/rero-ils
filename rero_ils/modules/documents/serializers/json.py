# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

from datetime import datetime

from flask import current_app, json, request, stream_with_context
from werkzeug.local import LocalProxy

from rero_ils.modules.documents.utils import process_i18n_literal_fields
from rero_ils.modules.documents.views import create_title_alternate_graphic, \
    create_title_responsibilites, create_title_variants
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.organisations.api import OrganisationsSearch
from rero_ils.modules.serializers import JSONSerializer

from ..dumpers import document_replace_refs_dumper
from ..dumpers.indexer import IndexerDumper
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

        # TODO: uses dumpers
        # build responsibility data for display purpose
        responsibility_statement = rec.get('responsibilityStatement', [])
        if responsibilities := create_title_responsibilites(
            responsibility_statement
        ):
            rec['ui_responsibilities'] = responsibilities
        titles = rec.get('title', [])
        if altgr_titles := create_title_alternate_graphic(titles):
            rec['ui_title_altgr'] = altgr_titles
        if altgr_titles_responsibilities := create_title_alternate_graphic(
            titles, responsibility_statement
        ):
            rec['ui_title_altgr_responsibilities'] = \
                                altgr_titles_responsibilities

        if variant_titles := create_title_variants(titles):
            rec['ui_title_variants'] = variant_titles

        data = super().preprocess_record(
            pid=pid, record=rec, links_factory=links_factory, kwargs=kwargs)
        metadata = data['metadata']
        resolve = request.args.get(
            'resolve',
            default=False,
            type=lambda v: v.lower() in ['true', '1']
        )
        if request and resolve:
            IndexerDumper()._process_host_document(None, metadata)
        return data

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process each hit of a search result."""
        view_id, view_code = DocumentJSONSerializer._get_view_information()
        metadata = hit.get('metadata', {})
        pid = metadata.get('pid')

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
            def extract_year(key, default):
                """Extract year from year aggregation.

                :param: key: the dict key.
                :param: default: the default year.
                :return: the year in yyyy format.
                """
                # default could be None
                if year := aggregations['year'][key].get('value'):
                    return float(year)
                return default

            # transform aggregation to send configuration
            # for ng-core range widget.
            # this allows you to fill in the fields on the frontend.
            aggregations['year'] = {
                'type': 'range',
                'config': {
                    'min': extract_year('year_min', 0.0),
                    'max': extract_year('year_max', 9999.9),
                    'step': 1
                }
            }

        if aggregations.get('acquisition'):
            # format the results of facet 'acquisition' to be displayed
            # as date range with min and max date (limit)
            def extract_acquisition_date(key, default):
                """Exact date from acquisition aggregation.

                :param: key: the dict key.
                :param: default: the default date.
                :return: the date in yyyy-MM-dd format.
                """
                return aggregations['acquisition'][key].get(
                    'value_as_string', aggregations['acquisition'][key].get(
                        'value', default))

            # transform aggregation to send configuration
            # for ng-core date-range widget.
            # this allows you to fill in the fields on the frontend.
            aggregations['acquisition'] = {
                'type': 'date-range',
                'config': {
                    'min': extract_acquisition_date('date_min', '1900-01-01'),
                    'max': extract_acquisition_date(
                        'date_max', datetime.now().strftime('%Y-%m-%d')
                    )
                }
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
        if contributions := record.pop('contribution', []):
            record['contribution'] = process_i18n_literal_fields(contributions)
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
