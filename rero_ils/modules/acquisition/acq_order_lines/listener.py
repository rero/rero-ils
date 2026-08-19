# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Order lines."""

from rero_ils.modules.acquisition.acq_order_lines.api import (
    AcqOrderLine,
    AcqOrderLinesSearch,
)


def enrich_acq_order_line_data(
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
    if index.split("-")[0] == AcqOrderLinesSearch.Meta.index:
        if not isinstance(record, AcqOrderLine):
            record = AcqOrderLine.get_record_by_pid(record.get("pid"))
        unreceived_quantity = record.unreceived_quantity
        # other dynamic keys
        json["total_unreceived_amount"] = round(unreceived_quantity * record["amount"], 2)
        json["status"] = record.status
        json["received_quantity"] = record.received_quantity
