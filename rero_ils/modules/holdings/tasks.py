# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Celery tasks for holdings records."""

from celery import shared_task
from flask import current_app

from ..utils import set_timestamp
from .api import Holding, HoldingsIndexer, HoldingsSearch


@shared_task(ignore_result=True)
def delete_standard_holdings_having_no_items():
    """Removes standard holdings records with no attached items."""
    search_query = HoldingsSearch().filter("term", holdings_type="standard").filter("term", items_count=0).source("pid")

    search_results = list(search_query.scan())
    count = len(search_results)
    deleted = 0
    errors = 0
    for hit in search_results:
        if record := Holding.get_record(hit.meta.id):
            try:
                record.delete(force=False, dbcommit=True, delindex=True)
                deleted += 1
            except Exception as err:
                errors += 1
                reasons = record.reasons_not_to_delete()
                current_app.logger.error(f"Cannot delete standard holding: {hit.pid} {reasons} {err}")
        else:
            # delete holding from index
            HoldingsIndexer().client.delete(id=hit.meta.id, index="holdings", doc_type="_doc")
            deleted += 1

    counts = {"count": count, "deleted": deleted, "errors": errors}
    set_timestamp("delete_standard_holdings_having_no_items", **counts)
    return counts
