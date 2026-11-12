# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tasks related to `Location` resources."""

from celery import shared_task

from rero_ils.modules.utils import extracted_data_from_ref


@shared_task(ignore_result=True)
def reindex_location_documents(location_pid):
    """Reindex the documents with holdings or temporary item locations on this location."""
    from rero_ils.modules.documents.api import DocumentsIndexer, DocumentsSearch
    from rero_ils.modules.holdings.api import HoldingsSearch
    from rero_ils.modules.items.api import ItemsSearch
    from rero_ils.modules.tasks import process_bulk_queue

    document_pids = set()
    for search, field in ((HoldingsSearch, "location__pid"), (ItemsSearch, "temporary_location__pid")):
        query = search().filter("term", **{field: location_pid}).source("document.pid")
        document_pids.update(hit.document.pid for hit in query.scan())
    if document_pids:
        query = DocumentsSearch().filter("terms", pid=list(document_pids)).source(False)
        DocumentsIndexer().bulk_index([hit.meta.id for hit in query.scan()])
        process_bulk_queue.apply_async()


@shared_task(ignore_result=True)
def remove_location_from_restriction(restricted_location):
    """Remove a location from pickup restriction for other locations.

    :param restricted_location: the location record to remove.
    :type: dict
    """
    from .api import Location, LocationsSearch

    # If the location is defined as a pickup location, no need to remove it
    # from restriction; just stop the process.
    if restricted_location.get("is_pickup", False):
        return

    # Search for locations that uses the restricted location into
    # `restrict_pickup_to` field. For each of these locations, remove the
    # restricted location from this field and reindex the record.
    restricted_pid = restricted_location["pid"]
    query = LocationsSearch().filter("term", restrict_pickup_to__pid=restricted_pid).source(False)
    for hit in query.scan():
        location = Location.get_record(hit.meta.id)
        restricted_location = [
            location_ref
            for location_ref in location["restrict_pickup_to"]
            if extracted_data_from_ref(location_ref) != restricted_pid
        ]
        del location["restrict_pickup_to"]
        if restricted_location:
            location["restrict_pickup_to"] = restricted_location
        location.update(location, dbcommit=True, reindex=True)
