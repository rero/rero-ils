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

"""Acquisition receipt line serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.acquisition.dumpers import document_acquisition_dumper
from rero_ils.modules.documents.api import Document
from rero_ils.modules.serializers import ACQJSONSerializer, \
    RecordSchemaJSONV1, search_responsify


class AcqReceiptLineJSONSerializer(ACQJSONSerializer):
    """Serializer for RERO-ILS `AcqReceiptLine` records as JSON."""

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process a specific search hit.

        :param hit: the dictionary representing an ElasticSearch search hit.
        """
        metadata = hit.get('metadata', {})
        if doc_pid := metadata.get('document', {}).get('pid'):
            document = Document.get_record_by_pid(doc_pid)
            metadata['document'] = document.dumps(
                dumper=document_acquisition_dumper)
        super()._postprocess_search_hit(hit)


_json = AcqReceiptLineJSONSerializer(RecordSchemaJSONV1)
json_acrl_search = search_responsify(_json, 'application/rero+json')
json_acrl_record = record_responsify(_json, 'application/rero+json')
