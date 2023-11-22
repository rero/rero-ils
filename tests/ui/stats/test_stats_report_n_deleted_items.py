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
    # created by the system user
    es.index(
        index="operation_logs-2020",
        id="1",
        body={
            "date": "2023-01-01",
            "operation": "delete",
            "record": {
                "type": "item",
                "library_pid": lib_martigny.pid,
                "organisation_pid": org_martigny.pid,
            },
            "user_name": "system",
        },
        refresh=True,
    )
    # legacy record do not contains record
    es.index(
        index="operation_logs-2020",
        id="2",
        body={
            "date": "2023-01-01",
            "operation": "create",
            "user_name": "Doe, John",
            "library": {
                "type": "lib",
                "value": lib_martigny.pid
            },
            "organisation": {
                "type": "org",
                "value": org_martigny.pid
            }
        },
        refresh=True,
    )
    es.index(
        index="operation_logs-2020",
        id="3",
        body={
            "date": "2023-01-01",
            "operation": "delete",
            "library": {"type": "lib", "value": lib_martigny.pid},
            "record": {
                "type": "holding",
                "library_pid": lib_martigny.pid,
                "organisation_pid": org_martigny.pid,
            },
        },
        refresh=True,
    )
    es.index(
        index="operation_logs-2020",
        id="4",
        body={
            "date": "2023-01-01",
            "operation": "delete",
            "library": {"type": "lib", "value": lib_sion.pid},
            "record": {
                "type": "holding",
                "library_pid": lib_sion.pid,
                "organisation_pid": org_sion.pid,
            },
        },
        refresh=True,
    )
    es.index(
        index="operation_logs-2020",
        id="5",
        body={
            "date": "2024-01-01",
            "operation": "delete",
            "library": {"type": "lib", "value": lib_martigny_bourg.pid},
            "record": {
                "type": "item",
                "library_pid": lib_martigny_bourg.pid,
                "organisation_pid": org_martigny.pid,
            },
        },
        refresh=True,
    )
    # no distributions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {"indicator": {"type": "number_of_deleted_items"}},
    }
    assert StatsReport(cfg).collect() == [[2]]

    # no distributions with filters
    lib_pid = lib_martigny_bourg.pid
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "filter_by_libraries": [
            {"$ref": f"https://bib.rero.ch/api/libraries/{lib_pid}"}
        ],
        "category": {"indicator": {"type": "number_of_deleted_items"}},
    }
    assert StatsReport(cfg).collect() == [[1]]

    # one distrubtions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["owning_library"],
            }
        },
    }
    assert StatsReport(cfg).collect() == [
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1],
    ]

    # one distrubtions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["operator_library"]
            }
        }
    }
    # do not contains system
    assert StatsReport(cfg).collect() == [
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 1]
    ]

    # two distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["owning_library", "action_month"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', '2023-01', '2024-01'],
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 0, 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1, 0]
    ]

    # reverse distrubtions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["action_month", "owning_library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
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
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "distributions": ["action_year", "owning_library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
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
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_deleted_items",
                "period": "year",
                "distributions": ["owning_library"]
            }
        }
    }
    with mock.patch(
        'rero_ils.modules.stats.api.report.datetime'
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(year=2024, month=1, day=1)
        assert StatsReport(cfg).collect() == [
            [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1]
        ]
