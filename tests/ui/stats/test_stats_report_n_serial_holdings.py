# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stats Report tests for number of serial holdings."""

from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_serial_holdings(org_martigny, org_sion, lib_martigny, lib_martigny_bourg, lib_sion):
    """Test the number of serials."""
    # no data
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {"indicator": {"type": "number_of_serial_holdings"}},
    }
    assert StatsReport(cfg).collect() == [[0]]

    # fixtures
    es.index(
        index="holdings",
        id="1",
        body={
            "_created": "2023-02-01",
            "holdings_type": "serial",
            "organisation": {"pid": org_martigny.pid},
            "library": {"pid": lib_martigny.pid},
        },
    )
    es.index(
        index="holdings",
        id="2",
        body={
            "_created": "2024-01-01",
            "holdings_type": "serial",
            "organisation": {"pid": org_martigny.pid},
            "library": {"pid": lib_martigny_bourg.pid},
        },
    )
    es.index(
        index="holdings",
        id="3",
        body={
            "_created": "2024-01-01",
            "holdings_type": "standard",
            "organisation": {"pid": org_martigny.pid},
            "library": {"pid": lib_martigny_bourg.pid},
        },
    )
    es.index(
        index="holdings",
        id="4",
        body={
            "_created": "2024-01-01",
            "holdings_type": "serial",
            "organisation": {"pid": org_sion.pid},
            "library": {"pid": lib_sion.pid},
        },
    )
    es.indices.refresh(index="holdings")

    # no distributions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {"indicator": {"type": "number_of_serial_holdings"}},
    }
    assert StatsReport(cfg).collect() == [[2]]

    # no distributions with filters
    lib_pid = lib_martigny_bourg.pid
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "filter_by_libraries": [{"$ref": f"https://bib.rero.ch/api/libraries/{lib_pid}"}],
        "category": {"indicator": {"type": "number_of_serial_holdings"}},
    }
    assert StatsReport(cfg).collect() == [[1]]

    # one distrubtions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings",
                "distributions": ["owning_library"],
            }
        },
    }
    assert StatsReport(cfg).collect() == [
        [f"{lib_martigny_bourg.get('name')} ({lib_martigny_bourg.pid})", 1],
        [f"{lib_martigny.get('name')} ({lib_martigny.pid})", 1],
    ]

    # two distributions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings",
                "distributions": ["owning_library", "created_month"],
            }
        },
    }
    assert StatsReport(cfg).collect() == [
        ["", "2023-02", "2024-01"],
        [f"{lib_martigny_bourg.get('name')} ({lib_martigny_bourg.pid})", 0, 1],
        [f"{lib_martigny.get('name')} ({lib_martigny.pid})", 1, 0],
    ]

    # reverse distrubtions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings",
                "distributions": ["created_month", "owning_library"],
            }
        },
    }
    assert StatsReport(cfg).collect() == [
        [
            "",
            f"{lib_martigny_bourg.get('name')} ({lib_martigny_bourg.pid})",
            f"{lib_martigny.get('name')} ({lib_martigny.pid})",
        ],
        ["2023-02", 0, 1],
        ["2024-01", 1, 0],
    ]

    # reverse distrubtions
    cfg = {
        "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings",
                "distributions": ["created_year", "owning_library"],
            }
        },
    }
    assert StatsReport(cfg).collect() == [
        [
            "",
            f"{lib_martigny_bourg.get('name')} ({lib_martigny_bourg.pid})",
            f"{lib_martigny.get('name')} ({lib_martigny.pid})",
        ],
        ["2023", 0, 1],
        ["2024", 1, 0],
    ]
