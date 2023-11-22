# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2023 UCL
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

"""Stats Report tests creation."""

from datetime import datetime

import mock

from rero_ils.modules.stats.api.api import Stat
from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_create(lib_martigny, document):
    """Test the stat report creation."""
    cfg = {
        "$schema":
            "https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json",
        "library": {
            "$ref": f"https://bib.rero.ch/api/libraries/{lib_martigny.pid}"
        },
        "is_active": True,
        "pid": "1",
        "name": "foo",
        "frequency": "month",
        "category": {
            "type": "catalog",
            "indicator": {
                "type": "number_of_documents",
                "distributions": ['owning_library']
            }
        }
    }
    assert StatsReport(cfg)
    cfg['is_active'] = False
    assert not StatsReport(cfg).collect()

    res = StatsReport(cfg).collect()
    assert Stat.create(data=dict(
        type='report',
        config=cfg,
        values=[dict(results=res)]
    ))


def test_stats_report_range(app, lib_martigny):
    """Test the report range period."""
    cfg = {
        "library": {
            "$ref": f"https://bib.rero.ch/api/libraries/{lib_martigny.pid}"
        },
        "category": {
            "indicator": {
                "type": "number_of_documents",
                "distributions": ["owning_library"]
            }
        }
    }
    with mock.patch(
        'rero_ils.modules.stats.api.report.datetime'
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(year=2023, month=2, day=1)
        assert StatsReport(cfg).get_range_period('month') == \
            dict(gte='2023-01-01T00:00:00', lte='2023-01-31T23:59:59')
        assert StatsReport(cfg).get_range_period('year') == \
            dict(gte='2022-01-01T00:00:00', lte='2022-12-31T23:59:59')
        mock_datetime.now.return_value = datetime(year=2023, month=1, day=5)
        assert StatsReport(cfg).get_range_period('month') == \
            dict(gte='2022-12-01T00:00:00', lte='2022-12-31T23:59:59')
        assert not StatsReport(cfg).get_range_period('foo')
