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

from rero_ils.modules.stats.api.api import Stat
from rero_ils.modules.stats.api.librarian import StatsForLibrarian
from rero_ils.modules.stats.api.pricing import StatsForPricing
from rero_ils.modules.stats.api.report import StatsReport


@pytest.fixture(scope='module')
def stats(item_lib_martigny, item_lib_fully, item_lib_sion,
          ill_request_martigny):
    """Stats fixture."""
    stats = StatsForPricing(to_date=arrow.utcnow())
    yield Stat.create(
        data=dict(
            type='billing',
            values=stats.collect()
        ),
        dbcommit=True,
        reindex=True
    )


@pytest.fixture(scope='module')
def stats_librarian(item_lib_martigny, item_lib_fully, item_lib_sion):
    """Stats fixture for librarian."""
    stats_librarian = StatsForLibrarian()
    date_range = {
        'from': stats_librarian.date_range['gte'],
        'to': stats_librarian.date_range['lte']
    }
    stats_values = stats_librarian.collect()
    yield Stat.create(
        data=dict(
            type='librarian',
            date_range=date_range,
            values=stats_values
        ),
        dbcommit=True,
        reindex=True
    )


@pytest.fixture(scope='module')
def stats_report_martigny(stats_cfg_martigny, item_lib_martigny):
    """Stats fixture for librarian."""
    stat_report = StatsReport(stats_cfg_martigny)
    values = stat_report.collect()
    yield stat_report.create_stat(values)
