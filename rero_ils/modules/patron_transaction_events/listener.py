# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Patron transaction event."""

from .api import PatronTransactionEvent, PatronTransactionEventsSearch


def enrich_patron_transaction_event_data(
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
    if index.split("-")[0] != PatronTransactionEventsSearch.Meta.index:
        return

    if not isinstance(record, PatronTransactionEvent):
        pid = record.get("pid")
        record = PatronTransactionEvent.get_record_by_pid(pid)

    parent = record.patron_transaction
    # Add information about the patron related to this event
    if patron := parent.patron:
        json["patron"] = {"pid": patron.pid, "type": "ptrn"}
        if barcode := patron.patron.get("barcode"):
            json["patron"]["barcode"] = barcode[0]
        if ptty_pid := patron.patron_type_pid:
            json["patron_type"] = {"pid": ptty_pid, "type": "ptty"}
    # Add information about the owning library related to the parent loan
    # (if exists) :: useful for faceting filter
    if (loan := parent.loan) and (item := loan.item):
        json["owning_library"] = {"pid": item.library_pid, "type": "lib"}
        json["owning_location"] = {"pid": item.location_pid, "type": "loc"}
        json["item"] = {"pid": parent.item_pid, "type": "item"}
        if barcode := item.get("barcode"):
            json["item"]["barcode"] = barcode
    # Add additional information
    json["organisation"] = {"pid": parent.organisation_pid, "type": "org"}
    json["category"] = parent["type"]
    if parent.document_pid:
        json["document"] = {"pid": parent.document_pid, "type": "doc"}
