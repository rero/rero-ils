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

"""Stats Report tests for number of items."""

from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_items(
        org_martigny, org_sion, lib_martigny, lib_martigny_bourg,
        lib_sion, loc_public_martigny, loc_restricted_martigny,
        loc_public_martigny_bourg, loc_public_sion):
    """Test the number of items."""
    # no data
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[0]]

    # fixtures
    es.index(index='items', id='1', body={
        '_created': "2023-02-01",
        'type': 'standard',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny.pid},
        'location': {'pid': loc_public_martigny.pid}
    })
    es.index(index='items', id='2', body={
        '_created': "2023-02-01",
        'type': 'issue',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny.pid},
        'location': {'pid': loc_restricted_martigny.pid}
    })
    es.index(index='items', id='3', body={
        '_created': "2024-01-01",
        'type': 'provisional',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny_bourg.pid},
        'location': {'pid': loc_public_martigny_bourg.pid}
    })
    es.index(index='items', id='4', body={
        '_created': "2024-01-01",
        'type': 'standard',
        'organisation': {'pid': org_sion.pid},
        'library': {'pid': lib_sion.pid},
        'location': {'pid': loc_public_sion.pid}
    })
    es.indices.refresh(index='items')

    # no distributions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[3]]

    # one distrubtions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items",
                "distributions": ["library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 2]
    ]

    # two distributions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items",
                "distributions": ["library", "created_month"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', '2023-02', '2024-01'],
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 0, 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 2, 0]
    ]

    # reverse distrubtions
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items",
                "distributions": ["created_month", "library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['2023-02', 0, 2],
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
                "type": "number_of_items",
                "distributions": ["created_year", "library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['2023', 0, 2],
        ['2024', 1, 0]
    ]

    # type
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items",
                "distributions": ["type", "library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['issue', 0, 1],
        ['provisional', 1, 0],
        ['standard', 0, 1]
    ]

    # location/type
    cfg = {
        "organisation": {
            "$ref": "https://bib.rero.ch/api/organisations/org1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_items",
                "distributions": ["type", "location"]
            }
        }
    }
    label_loc_pub_martigny = f'{lib_martigny["name"]} / '\
        f'{loc_public_martigny["name"]} ({loc_public_martigny.pid})'
    label_loc_rest_martigny = f'{lib_martigny["name"]} / '\
        f'{loc_restricted_martigny["name"]} ({loc_restricted_martigny.pid})'
    label_loc_pub_martigny_bourg = f'{lib_martigny_bourg["name"]} / '\
        f'{loc_public_martigny_bourg["name"]} '\
        f'({loc_public_martigny_bourg.pid})'
    assert StatsReport(cfg).collect() == [
        [
            '',
            label_loc_pub_martigny_bourg,
            label_loc_pub_martigny,
            label_loc_rest_martigny
        ],
        ['issue', 0, 0, 1],
        ['provisional', 1, 0, 0],
        ['standard', 0, 1, 0]
    ]
