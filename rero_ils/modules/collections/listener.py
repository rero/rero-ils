# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Collection."""

from ..utils import extracted_data_from_ref
from .api import Collection, CollectionsSearch


def enrich_collection_data(sender, json=None, record=None, index=None, doc_type=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split("-")[0] == CollectionsSearch.Meta.index:
        collection = record
        if not isinstance(record, Collection):
            collection = Collection.get_record_by_pid(record.get("pid"))
        json["organisation"] = {
            "pid": extracted_data_from_ref(collection.get("organisation")),
            "type": "org",
        }
