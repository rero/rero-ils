# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Pytest fixtures for stats REST tests."""

import arrow
import pytest

from rero_ils.modules.stats.api.librarian import StatsForLibrarian
from rero_ils.modules.stats.api.pricing import StatsForPricing


@pytest.fixture(scope='module')
def stat_for_pricing(document, lib_martigny):
    """Stats for Pricing."""
    yield StatsForPricing(to_date=arrow.utcnow())


@pytest.fixture(scope='module')
def stat_for_librarian(document, lib_martigny):
    """Stats for Librarian."""
    yield StatsForLibrarian(to_date=arrow.utcnow())
