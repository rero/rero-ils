# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities functions about `Holdings` resource."""

from datetime import UTC, datetime, timedelta

from flask import current_app

from rero_ils.modules.errors import RegularReceiveNotAllowed
from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.items.models import ItemIssueStatus


def get_late_serial_holdings():
    """Return serial holdings with late issues.

    Holdings are considered late if :
      * holding type is `serial`
      * it's a `regular` serial holding (exclude irregular type)
      * it's considered as alive (acq_status='currently_received')
      * next expected date has passed (greater than current datetime).

    :return: A `Holding` resource generator
    """
    yesterday = datetime.now(UTC) - timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")
    query = (
        HoldingsSearch()
        .filter("term", holdings_type="serial")
        .filter("term", acquisition_status="currently_received")
        .filter("range", patterns__next_expected_date={"lte": yesterday})
        .source(False)
    )
    for id_ in [hit.meta.id for hit in query.scan()]:
        yield Holding.get_record(id_)


def create_next_late_expected_issues(dbcommit=False, reindex=False):
    """Receive the next late expected issue for all holdings.

    :param reindex: reindex record by record.
    :param dbcommit: commit record to database.
    :return: the number of created issues.
    """
    counter = 0
    for holding in get_late_serial_holdings():
        try:
            holding.create_regular_issue(status=ItemIssueStatus.LATE, dbcommit=dbcommit, reindex=reindex)
            counter += 1
        except RegularReceiveNotAllowed as err:
            pid = holding.pid
            msg = f"Cannot receive next expected issue for Holding#{pid}"
            current_app.logger.error(f"{msg}::{err!s}")
    return counter
