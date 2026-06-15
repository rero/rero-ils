# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO Document serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.documents.serializers.dc import DublinCoreSerializer
from rero_ils.modules.documents.serializers.json import (
    DocumentExportJSONSerializer,
    DocumentJSONSerializer,
)
from rero_ils.modules.documents.serializers.marc import (
    DocumentMARCXMLSerializer,
    DocumentMARCXMLSRUSerializer,
)
from rero_ils.modules.documents.serializers.ris import RISSerializer
from rero_ils.modules.serializers import (
    RecordSchemaJSONV1,
    record_responsify_file,
    search_responsify,
    search_responsify_file,
)

# Serializers
# ===========
_json = DocumentJSONSerializer(RecordSchemaJSONV1)
_json_export = DocumentExportJSONSerializer()
_xml_dc = DublinCoreSerializer(RecordSchemaJSONV1)
_xml_marcxml = DocumentMARCXMLSerializer()
_xml_marcxmlsru = DocumentMARCXMLSRUSerializer()
ris_serializer = RISSerializer()

# Records-REST serializers
# ========================
json_doc_search = search_responsify(_json, "application/rero+json")
json_doc_response = record_responsify(_json, "application/rero+json")
json_export_doc_search = search_responsify_file(
    _json_export, "application/export+json", file_extension="json", file_prefix="export"
)
json_export_doc_response = record_responsify_file(
    _json_export, "application/export+json", file_extension="json", file_prefix="export"
)

ris_doc_search = search_responsify_file(
    ris_serializer,
    "application/x-research-info-systems",
    file_extension="ris",
    file_prefix="export",
)
ris_doc_response = record_responsify_file(
    ris_serializer,
    "application/x-research-info-systems",
    file_extension="ris",
    file_prefix="export",
)

xml_dc_search = search_responsify(_xml_dc, "application/xml")
xml_dc_response = record_responsify(_xml_dc, "application/xml")

xml_marcxml_search = search_responsify(_xml_marcxml, "application/xml")
xml_marcxml_response = record_responsify(_xml_marcxml, "application/xml")
xml_marcxmlsru_search = search_responsify(_xml_marcxmlsru, "application/xml")
