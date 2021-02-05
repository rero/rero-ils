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

"""Document serialization."""

from flask import current_app, request
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from .utils import create_contributions, filter_document_type_buckets
from ..documents.api import Document
from ..documents.utils import title_format_text_head
from ..documents.views import create_title_alternate_graphic, \
    create_title_responsibilites, create_title_variants
from ..libraries.api import Library
from ..organisations.api import Organisation
from ..serializers import JSONSerializer, RecordSchemaJSONV1


class DocumentJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        rec = record
        titles = rec.get('title', [])
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
        # Item filters.
        viewcode = request.args.get('view',  current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
        ))
        records = results.get('hits', {}).get('hits', {})
        for record in records:
            metadata = record.get('metadata', {})
            available = Document.get_record_by_pid(
                metadata.get('pid')).is_available(viewcode)
            metadata['available'] = available
            titles = metadata.get('title', [])
            text_title = title_format_text_head(titles, with_subtitle=False)
            if text_title:
                metadata['ui_title_text'] = text_title
            responsibility = metadata.get('responsibilityStatement', [])
            text_title = title_format_text_head(titles, responsibility,
                                                with_subtitle=False)
            if text_title:
                metadata['ui_title_text_responsibility'] = text_title

        if viewcode != current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
        ):
            view_id = Organisation.get_record_by_viewcode(viewcode)['pid']
            for record in records:
                metadata = record.get('metadata', {})
                items = metadata.get('items', [])
                if items:
                    output = []
                    for item in items:
                        if item.get('organisation')\
                                .get('organisation_pid') == view_id:
                            output.append(item)
                    record['metadata']['items'] = output

        # Add organisation name
        for org_term in results.get('aggregations', {}).get(
                'organisation', {}).get('buckets', []):
            pid = org_term.get('key')
            org = Organisation.get_record_by_pid(pid)
            name = org.get('name')
            org_term['name'] = name
            lib_buckets = self._process_library_buckets(org, org_term.get(
                'library', {}).get('buckets', [])
            )
            if lib_buckets:
                org_term['library']['buckets'] = lib_buckets

        # TODO: Move this logic in the front end (needs backend adaptation)
        if (viewcode is not None) and (viewcode != current_app.config.get(
            'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
        )):
            org = Organisation.get_record_by_viewcode(viewcode)
            org_buckets = results.get('aggregations', {}).get(
                'organisation', {}).get('buckets', [])
            for bucket in org_buckets:
                if bucket.get('key') == org.pid:
                    lib_agg = bucket.get('library')
                    if lib_agg:
                        results['aggregations']['library'] = lib_agg
                        del results['aggregations']['organisation']

        # Correct document type buckets
        new_type_buckets = []
        type_buckets = results['aggregations']['document_type']['buckets']
        results['aggregations']['document_type']['buckets'] = \
        filter_document_type_buckets(type_buckets)


        return super(
            DocumentJSONSerializer, self).post_process_serialize_search(
                results, pid_fetcher)

    @classmethod
    def _process_library_buckets(cls, org, lib_buckets):
        """Process library buckets.

        Add library names
        :param org: current organisation
        :param lib_buckets: library buckets

        :return processed buckets
        """
        processed_buckets = []
        lib_pids = list(org.get_libraries_pids())
        for bucket in lib_buckets:
            if bucket.get('key') in lib_pids:
                bucket['name'] = Library.get_record_by_pid(
                    bucket.get('key')).get('name')
                processed_buckets.append(bucket)

        return processed_buckets


json_doc = DocumentJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_doc_search = search_responsify(json_doc, 'application/rero+json')
json_doc_response = record_responsify(json_doc, 'application/rero+json')
