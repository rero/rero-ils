# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures for stats REST tests."""

import arrow
import pytest

from rero_ils.modules.stats.api.api import Stat
from rero_ils.modules.stats.api.librarian import StatsForLibrarian
from rero_ils.modules.stats.api.pricing import StatsForPricing


@pytest.fixture(scope="module")
def stat_for_pricing(document, lib_martigny):
    """Stats for Pricing."""
    yield StatsForPricing(to_date=arrow.utcnow())


@pytest.fixture(scope="module")
def stat_for_librarian(document, lib_martigny):
    """Stats for Librarian."""
    yield StatsForLibrarian(to_date=arrow.utcnow())


@pytest.fixture(scope="module")
def stats_librarian(item_lib_martigny, item_lib_fully, item_lib_sion):
    """Saved statistics record for librarian export views."""
    stats_librarian = StatsForLibrarian()
    date_range = {
        "from": stats_librarian.date_range["gte"],
        "to": stats_librarian.date_range["lte"],
    }
    yield Stat.create(
        data={
            "type": "librarian",
            "date_range": date_range,
            "values": stats_librarian.collect(),
        },
        dbcommit=True,
        reindex=True,
    )
