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

from rero_ils.modules.stats.api import Stat, StatsForPricing


@pytest.fixture(scope='module')
def stats(item_lib_martigny, item_lib_fully, item_lib_sion):
    """Stats fixture."""
    stats = StatsForPricing(to_date=arrow.utcnow())
    yield Stat.create(
        dict(values=stats.collect()), dbcommit=True, reindex=True)
