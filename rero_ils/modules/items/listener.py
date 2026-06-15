# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Item."""

from rero_ils.modules.documents.api import Document
from rero_ils.modules.local_fields.api import LocalField
from rero_ils.modules.local_fields.dumpers import (
    ElasticSearchDumper as LocalFieldESDumper,
)

from .api import Item, ItemsSearch


def enrich_item_data(
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
    if index.split("-")[0] != ItemsSearch.Meta.index:
        return
    if not isinstance(record, Item):
        record = Item.get_record_by_pid(record.get("pid"))

    # Document type
    document = Document.get_record_by_pid(json["document"]["pid"])
    json["document"]["document_type"] = document["type"]

    # Current pending requests
    json["current_pending_requests"] = record.get_requests(output="count")

    if local_fields := [field.dumps(dumper=LocalFieldESDumper()) for field in LocalField.get_local_fields(record)]:
        json["local_fields"] = local_fields

    if record.is_issue:
        # `sort_key` used exclusively for search sorting.
        json["issue"]["sort_key"] = record.sort_date or record.expected_date
        # inherited_first_call_number to issue
        if call_number := record.issue_inherited_first_call_number:
            json["issue"]["inherited_first_call_number"] = call_number
        # inherited_second_call_number to issue
        if call_number := record.issue_inherited_second_call_number:
            json["issue"]["inherited_second_call_number"] = call_number
        # inject vendor pid
        if vendor_pid := record.vendor_pid:
            json["vendor"] = {"pid": vendor_pid, "type": "vndr"}
        # inject claims information: counter and dates
        notifications = record.claim_notifications
        claims_data = {"counter": len(notifications) if notifications else 0}
        if notifications and (
            dates := [
                notification["creation_date"] for notification in notifications if "creation_date" in notification
            ]
        ):
            claims_data["dates"] = dates
        json["issue"]["claims"] = claims_data

    if sort_call_number := json.get("call_number") or json.get("issue", {}).get("inherited_first_call_number"):
        json["sort_call_number"] = sort_call_number
    if sort_second_call_number := json.get("second_call_number") or json.get("issue", {}).get(
        "inherited_second_call_number"
    ):
        json["sort_second_call_number"] = sort_second_call_number
