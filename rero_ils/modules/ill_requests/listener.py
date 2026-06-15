# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Item."""

from ..locations.api import Location
from ..utils import extracted_data_from_ref
from .api import ILLRequest, ILLRequestsSearch


def enrich_ill_request_data(sender, json=None, record=None, index=None, doc_type=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split("-")[0] == ILLRequestsSearch.Meta.index:
        if not isinstance(record, ILLRequest):
            record = ILLRequest.get_record_by_pid(record.get("pid"))
        json["organisation"] = {"pid": record.organisation_pid}
        # add patron name to search index (for faceting)
        patron = extracted_data_from_ref(record.get("patron").get("$ref"), "record")
        json["patron"]["name"] = patron.formatted_name
        if loc_pid := json.get("pickup_location", {}).get("pid"):
            parent_lib = Location.get_record_by_pid(loc_pid).get_library()
            json["library"] = {"pid": parent_lib.pid}
