# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipt serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.acquisition.acq_receipt_lines.dumpers import (
    AcqReceiptLineESDumper,
)
from rero_ils.modules.serializers import ACQJSONSerializer, RecordSchemaJSONV1


class AcqReceiptReroJSONSerializer(ACQJSONSerializer):
    """Serializer for RERO-ILS `AcqReceipt` records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        # add some dynamic key related to the record.
        record["total_amount"] = record.total_amount
        record["quantity"] = record.total_item_quantity
        record["receipt_lines"] = [
            receipt_line.dumps(dumper=AcqReceiptLineESDumper()) for receipt_line in record.get_receipt_lines()
        ]
        # add currency to avoid to load related order_line->order to get it
        record["currency"] = record.order.get("currency")

        return super().preprocess_record(pid=pid, record=record, links_factory=links_factory, kwargs=kwargs)


_json = AcqReceiptReroJSONSerializer(RecordSchemaJSONV1)
json_acre_record = record_responsify(_json, "application/rero+json")
