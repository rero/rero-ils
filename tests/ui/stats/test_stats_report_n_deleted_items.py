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

"""Stats Report tests for number of deleted items."""

from datetime import datetime

import mock
from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_deleted_items(
        org_martigny, org_sion, lib_martigny, lib_martigny_bourg,
        lib_sion):
    """Test the number of deleted items."""
    # fixtures
    es.index(index='operation_logs-2020', id='1', body={
        "date": "2023-01-01",
        "library": {
          "value": lib_martigny.pid
        },
        "operation": "delete",
        "organisation": {
          "value": org_martigny.pid
        },
        "record": {
          "type": "item",
        }
    }, refresh=True)
    es.index(index='operation_logs-2020', id='2', body={
        "date": "2023-01-01",
        "library": {
          "value": lib_martigny.pid
        },
        "operation": "create",
        "organisation": {
          "value": org_martigny.pid
        },
        "record": {
          "type": "item",
        }
    }, refresh=True)
    es.index(index='operation_logs-2020', id='3', body={
        "date": "2023-01-01",
        "library": {
          "value": lib_martigny.pid
        },
        "operation": "delete",
        "organisation": {
          "value": org_martigny.pid
        },
        "record": {
          "type": "holding",
        }
    }, refresh=True)
    es.index(index='operation_logs-2020', id='4', body={
        "date": "2023-01-01",
        "library": {
          "value": lib_sion.pid
        },
        "operation": "delete",
        "organisation": {
          "value": org_sion.pid
        },
        "record": {
          "type": "holding",
        }
    }, refresh=True)
    es.index(index='operation_logs-2020', id='5', body={
        "date": "2024-01-01",
        "library": {
          "value": lib_martigny_bourg.pid
        },
        "operation": "delete",
        "organisation": {
          "value": org_martigny.pid
        },
        "record": {
          "type": "item",
        }
    }, refresh=True)
    # no distributions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items"
            }
        }
    }
    assert StatsReport(cfg).compute() == [[2]]

    # one distrubtions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["library"]
            }
        }
    }
    assert StatsReport(cfg).compute() == [
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1]
    ]

    # two distributions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["library", "action_month"]
            }
        }
    }
    assert StatsReport(cfg).compute() == [
        ['', '2023-01', '2024-01'],
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 0, 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1, 0]
    ]

    # reverse distrubtions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["action_month", "library"]
            }
        }
    }
    assert StatsReport(cfg).compute() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['2023-01', 0, 1],
        ['2024-01', 1, 0]
    ]

    # year
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["action_year", "library"]
            }
        }
    }
    assert StatsReport(cfg).compute() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['2023', 0, 1],
        ['2024', 1, 0]
    ]

    # limit by period
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "period": "year",
                "distributions": ["library"]
            }
        }
    }
    with mock.patch(
        'rero_ils.modules.stats.api.report.datetime'
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(year=2024, month=1, day=1)
        assert StatsReport(cfg).compute() == [
            [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1]
        ]
