# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Patron transaction."""

from .api import PatronTransaction, PatronTransactionsSearch


def enrich_patron_transaction_data(
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
    if index.split("-")[0] != PatronTransactionsSearch.Meta.index:
        return

    if not isinstance(record, PatronTransaction):
        record = PatronTransaction.get_record_by_pid(record.get("pid"))

    if barcode := record.patron.patron.get("barcode"):
        json["patron"]["barcode"] = barcode[0]

    if loan := record.loan:
        json["document"] = {"pid": record.document_pid, "type": "doc"}
        json["library"] = {"pid": record.library_pid, "type": "lib"}
        json["item"] = {"pid": loan.item_pid, "type": "item"}
