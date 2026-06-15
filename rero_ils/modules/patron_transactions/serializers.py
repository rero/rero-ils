# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transactions serialization."""

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.items.api.api import Item
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.serializers import (
    CachedDataSerializerMixin,
    JSONSerializer,
    RecordSchemaJSONV1,
    search_responsify,
)


class PatronTransactionsJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `PatronTransaction` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result.

        :param hit: the dictionary representing an ElasticSearch search hit.
        """
        metadata = hit.get("metadata", {})
        # Serialize document (if exists)
        document_pid = metadata.get("document", {}).get("pid")
        if document_pid and (document := self.get_resource(DocumentsSearch(), document_pid)):
            metadata["document"] = document
        # Serialize loan & item
        loan_pid = metadata.get("loan", {}).get("pid")
        if loan_pid and (loan := self.get_resource(Loan, loan_pid)):
            metadata["loan"] = loan
            item_pid = loan.get("item_pid", {}).get("value")
            if item := self.get_resource(Item, item_pid):
                metadata["loan"]["item"] = item
        super()._postprocess_search_hit(hit)


_json = PatronTransactionsJSONSerializer(RecordSchemaJSONV1)
json_pttr_search = search_responsify(_json, "application/rero+json")
