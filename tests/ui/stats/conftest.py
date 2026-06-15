# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures for stats REST tests."""

import arrow
import pytest

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
