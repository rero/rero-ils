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

"""Document serializers."""

from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from rero_ils.modules.documents.serializers.dc import DublinCoreSerializer
from rero_ils.modules.documents.serializers.json import \
    DocumentExportJSONSerializer, DocumentJSONSerializer
from rero_ils.modules.documents.serializers.marcxml import \
    DocumentMARCXMLSerializer, DocumentMARCXMLSRUSerializer
from rero_ils.modules.documents.serializers.ris import RISSerializer
from rero_ils.modules.response import record_responsify_file, \
    search_responsify_file
from rero_ils.modules.serializers import RecordSchemaJSONV1

# Serializers
# ===========
json_doc = DocumentJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""
json_export_doc = DocumentExportJSONSerializer()
"""JSON v1 serializer."""
xml_dc = DublinCoreSerializer(RecordSchemaJSONV1)
"""XML DUBLIN CORE v1 serializer."""
xml_marcxml = DocumentMARCXMLSerializer()
"""XML MARCXML v1 serializer."""
xml_marcxmlsru = DocumentMARCXMLSRUSerializer()
"""XML MARCXML SRU v1 serializer."""
ris_v1 = RISSerializer()
"""RIS v1 serializer."""

# Records-REST serializers
# ========================
json_doc_search = search_responsify(json_doc, 'application/rero+json')
json_doc_response = record_responsify(json_doc, 'application/rero+json')
json_export_doc_search = \
    search_responsify_file(json_export_doc, 'application/export+json', 'json')
json_export_doc_response = \
    record_responsify_file(json_export_doc, 'application/export+json', 'json')
ris_doc_search = \
    search_responsify_file(ris_v1,
                           'application/x-research-info-systems', 'ris')
ris_doc_response = \
    record_responsify_file(ris_v1,
                           'application/x-research-info-systems', 'ris')
xml_dc_search = search_responsify(xml_dc, 'application/xml')
xml_dc_response = record_responsify(xml_dc, 'application/xml')
xml_marcxml_search = search_responsify(xml_marcxml, 'application/xml')
xml_marcxml_response = record_responsify(xml_marcxml, 'application/xml')
xml_marcxmlsru_search = search_responsify(xml_marcxmlsru, 'application/xml')
