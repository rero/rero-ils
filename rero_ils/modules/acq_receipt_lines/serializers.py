# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Acquisition receipt line serialization."""

from invenio_records_rest.serializers.response import search_responsify

from ..documents.api import Document
from ..documents.dumpers import DocumentAcquisitionDumper
from ..serializers import JSONSerializer, RecordSchemaJSONV1


class AcqReceiptLineReroJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        records = results.get('hits', {}).get('hits', {})
        doc_dumper = DocumentAcquisitionDumper()
        for record in records:
            metadata = record.get('metadata', {})
            doc_pid = metadata.get('document', {}).get('pid')
            if doc_pid:
                document = Document.get_record_by_pid(doc_pid)
                metadata['document'] = document.dumps(dumper=doc_dumper)
        return results


json_acrl = AcqReceiptLineReroJSONSerializer(RecordSchemaJSONV1)
json_acrl_search = search_responsify(json_acrl, 'application/rero+json')
