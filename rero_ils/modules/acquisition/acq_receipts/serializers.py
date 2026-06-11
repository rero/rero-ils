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

"""Acquisition receipt serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.acquisition.acq_receipt_lines.dumpers import (
    AcqReceiptLineESDumper,
)
from rero_ils.modules.serializers import ACQJSONSerializer, AmountMixin, RecordSchemaJSONV1


class AcqReceiptReroJSONSerializer(AmountMixin, ACQJSONSerializer):
    """Serializer for RERO-ILS `AcqReceipt` records as JSON."""

    _amount_fields = ["amount_adjustments.amount", "total_amount"]

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        # add some dynamic key related to the record.
        record["total_amount"] = record.total_amount
        record["quantity"] = record.total_item_quantity
        receipt_lines = [
            receipt_line.dumps(dumper=AcqReceiptLineESDumper()) for receipt_line in record.get_receipt_lines()
        ]
        for line in receipt_lines:
            if isinstance(line.get("amount"), int):
                line["amount"] = round(line["amount"] / 100, 2)
        record["receipt_lines"] = receipt_lines
        # add currency to avoid to load related order_line->order to get it
        record["currency"] = record.order.get("currency")

        return super().preprocess_record(pid=pid, record=record, links_factory=links_factory, kwargs=kwargs)


_json = AcqReceiptReroJSONSerializer(RecordSchemaJSONV1)
json_acre_record = record_responsify(_json, "application/rero+json")
