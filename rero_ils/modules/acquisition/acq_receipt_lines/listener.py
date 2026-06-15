# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Acq receipt lines."""

from rero_ils.modules.acquisition.acq_receipt_lines.api import (
    AcqReceiptLine,
    AcqReceiptLinesSearch,
)


def enrich_acq_receipt_line_data(
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
    :param doc_type: The doc_type for the record.
    """
    if index.split("-")[0] == AcqReceiptLinesSearch.Meta.index:
        if not isinstance(record, AcqReceiptLine):
            record = AcqReceiptLine.get_record_by_pid(record.get("pid"))
        # other dynamic keys
        json.update(
            {
                "acq_account": {"pid": record.order_line.account_pid, "type": "acac"},
                "document": {"pid": record.order_line.document_pid, "type": "doc"},
                "total_amount": record.total_amount,
            }
        )
