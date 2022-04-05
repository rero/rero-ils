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

"""JSON Document serialization."""

from flask import current_app, request

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.utils import create_contributions, \
    filter_document_type_buckets, title_format_text_head
from rero_ils.modules.documents.views import create_title_alternate_graphic, \
    create_title_responsibilites, create_title_variants, subject_format
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.organisations.api import OrganisationsSearch
from rero_ils.modules.serializers import JSONSerializer


class DocumentJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

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
        if request and request.args.get('resolve') == '1':
            # We really have to replace the refs for the MEF here!
            rec_refs = record.replace_refs()
            contributions = create_contributions(
                rec_refs.get('contribution', [])
            )
            if contributions:
                rec['contribution'] = contributions

        return super().preprocess_record(
            pid=pid, record=rec, links_factory=links_factory, kwargs=kwargs)

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        view_id = None
        global_view_code = current_app.config.get(
            'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE')
        viewcode = request.args.get('view', global_view_code)
        if viewcode != global_view_code:
            # Maybe one more if here!
            view_id = OrganisationsSearch()\
                .get_record_by_viewcode(viewcode, 'pid').pid
        records = results.get('hits', {}).get('hits', {})
        for record in records:
            metadata = record.get('metadata', {})
            metadata['available'] = Document.is_available(
                metadata.get('pid'), viewcode)
            titles = metadata.get('title', [])
            text_title = title_format_text_head(titles, with_subtitle=False)
            if text_title:
                metadata['ui_title_text'] = text_title
            responsibility = metadata.get('responsibilityStatement', [])
            text_title = title_format_text_head(titles, responsibility,
                                                with_subtitle=False)
            if text_title:
                metadata['ui_title_text_responsibility'] = text_title

            if viewcode != global_view_code:
                record['metadata']['items'] = [
                    item for item in metadata.get('items', [])
                    if item['organisation'].get('organisation_pid') == view_id
                ]

        # Aggregations process
        if viewcode == global_view_code:
            # Global view
            aggr_org = request.args.getlist('organisation')
            for org_term in results.get('aggregations', {}) \
                    .get('organisation', {}).get('buckets', []):
                pid = org_term.get('key')
                org_term['name'] = OrganisationsSearch() \
                    .get_record_by_pid(pid, ['name']).name
                if pid not in aggr_org:
                    org_term.get('library', {}).pop('buckets', None)
                else:
                    org_term['library']['buckets'] = self \
                        ._process_library_buckets(
                        pid,
                        org_term.get('library', {}).get('buckets', [])
                    )
        else:
            # Local view
            aggregations = results.get('aggregations', {})
            for org_term in aggregations.get('organisation', {}) \
                    .get('buckets', {}):
                org_pid = org_term.get('key')
                if org_pid != view_id:
                    org_term.get('library', {}).pop('buckets', None)
                else:
                    # Add library aggregations
                    aggregations.setdefault('library', {}) \
                        .setdefault('buckets', self._process_library_buckets(
                            org_pid,
                            org_term.get('library', {}).get('buckets', [])
                        ))
                    # Remove organisation aggregation
                    aggregations.pop('organisation', None)

        # Correct document type buckets
        type_buckets = results[
            'aggregations'].get('document_type', {}).get('buckets')
        if type_buckets:
            results['aggregations']['document_type']['buckets'] = \
                filter_document_type_buckets(type_buckets)

        return super().post_process_serialize_search(results, pid_fetcher)

    @classmethod
    def _process_library_buckets(cls, org, lib_buckets):
        """Process library buckets.

        Add library names
        :param org: current organisation
        :param lib_buckets: library buckets

        :return processed buckets
        """
        lib_processed_buckets = []
        # get the library names for a given organisation
        records = LibrariesSearch()\
            .get_libraries_by_organisation_pid(org, ['pid', 'name'])
        libraries = {record.pid: record.name for record in records}
        # for all library bucket for a given organisation
        for lib_bucket in lib_buckets:
            lib_key = lib_bucket.get('key')
            # add the library name
            if lib_key in libraries:
                lib_bucket['name'] = libraries[lib_key]
                # process locations if exists
                if lib_bucket.get('location'):
                    lib_bucket['location']['buckets'] = \
                        cls._process_location_buckets(
                            lib_key,
                            lib_bucket.get('location', {}).get('buckets', []))
                # library is filterd by organisation
                lib_processed_buckets.append(lib_bucket)
        return lib_processed_buckets

    @classmethod
    def _process_location_buckets(cls, lib, loc_buckets):
        """Process location buckets.

        Add location names
        :param lib: current library pid
        :param loc_buckets: location buckets

        :return: processed buckets
        """
        # get the location names for a given library
        query = LocationsSearch() \
            .filter('term', library__pid=lib) \
            .source(['pid', 'name'])
        locations = {hit.pid: hit.name for hit in query.scan()}

        loc_processed_buckets = []
        # for all location bucket for a given library
        for loc_bucket in loc_buckets:
            loc_key = loc_bucket.get('key')
            # add the location name
            if loc_key in locations:
                loc_bucket['name'] = locations.get(loc_key)
                # location is filterd by library
                loc_processed_buckets.append(loc_bucket)
        return loc_processed_buckets
