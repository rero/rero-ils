# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for acquisition receipt."""

from rero_ils.modules.acquisition.acq_receipt_lines.dumpers import (
    AcqReceiptLineESDumper,
)

from .api import AcqReceiptsSearch


def enrich_acq_receipt_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The document type of the record.
    """
    if index.split("-")[0] == AcqReceiptsSearch.Meta.index:
        # add related order lines metadata
        json["receipt_lines"] = [
            receipt_line.dumps(dumper=AcqReceiptLineESDumper()) for receipt_line in record.get_receipt_lines()
        ]
        # other dynamic keys
        json["total_amount"] = record.total_amount
        json["quantity"] = record.total_item_quantity
