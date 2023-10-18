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

"""Stats Report tests for number of serial holdings."""

from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_serial_holdings(
        org_martigny, org_sion, lib_martigny, lib_martigny_bourg,
        lib_sion):
    """Test the number of serials."""
    # no data
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings"
            }
        }
    }
    assert StatsReport(cfg).compute() == [[0]]

    # fixtures
    es.index(index='holdings', id='1', body={
        '_created': "2023-02-01",
        'holdings_type': 'serial',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny.pid}
    })
    es.index(index='holdings', id='2', body={
        '_created': "2024-01-01",
        'holdings_type': 'serial',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny_bourg.pid}
    })
    es.index(index='holdings', id='3', body={
        '_created': "2024-01-01",
        'holdings_type': 'standard',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny_bourg.pid}
    })
    es.index(index='holdings', id='4', body={
        '_created': "2024-01-01",
        'holdings_type': 'serial',
        'organisation': {'pid': org_sion.pid},
        'library': {'pid': lib_sion.pid}
    })
    es.indices.refresh(index='holdings')

    # no distributions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings"
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
                "type": "number_of_serial_holdings",
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
                "type": "number_of_serial_holdings",
                "distributions": ["library", "created_month"]
            }
        }
    }
    assert StatsReport(cfg).compute() == [
        ['', '2023-02', '2024-01'],
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
                "type": "number_of_serial_holdings",
                "distributions": ["created_month", "library"]
            }
        }
    }
    assert StatsReport(cfg).compute() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['2023-02', 0, 1],
        ['2024-01', 1, 0]
    ]

    # reverse distrubtions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_serial_holdings",
                "distributions": ["created_year", "library"]
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
