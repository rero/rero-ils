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

"""Stats Report tests for number of ill requests."""


from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_ill_requests(
        org_martigny, org_sion, lib_martigny, lib_martigny_bourg, lib_sion,
        loc_public_martigny, loc_restricted_martigny,
        loc_public_martigny_bourg, loc_public_sion):
    """Test the number of ill requests."""
    label_loc_pub_martigny = f'{lib_martigny["name"]} / '\
        f'{loc_public_martigny["name"]} ({loc_public_martigny.pid})'
    label_loc_rest_martigny = f'{lib_martigny["name"]} / '\
        f'{loc_restricted_martigny["name"]} ({loc_restricted_martigny.pid})'
    label_loc_pub_martigny_bourg = f'{lib_martigny_bourg["name"]} / '\
        f'{loc_public_martigny_bourg["name"]} '\
        f'({loc_public_martigny_bourg.pid})'
    # no data
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[0]]

    # fixtures
    es.index(index='ill_requests', id='1', body={
        '_created': "2023-02-01",
        'status': 'pending',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny.pid},
        'pickup_location': {'pid': loc_public_martigny.pid}
    })
    es.index(index='ill_requests', id='2', body={
        '_created': "2023-02-01",
        'status': 'validated',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny.pid},
        'pickup_location': {'pid': loc_restricted_martigny.pid}
    })
    es.index(index='ill_requests', id='3', body={
        '_created': "2024-01-01",
        'status': 'closed',
        'organisation': {'pid': org_martigny.pid},
        'library': {'pid': lib_martigny_bourg.pid},
        'pickup_location': {'pid': loc_public_martigny_bourg.pid}
    })
    es.index(index='ill_requests', id='4', body={
        '_created': "2024-01-01",
        'status': 'denied',
        'organisation': {'pid': org_sion.pid},
        'library': {'pid': lib_sion.pid},
        'pickup_location': {'pid': loc_public_sion.pid}
    })
    es.indices.refresh(index='ill_requests')

    # no distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[3]]

    # no distributions with filters
    lib_pid = lib_martigny_bourg.pid
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "filter_by_libraries": [{
            '$ref':
                f'https://bib.rero.ch/api/libraries/{lib_pid}'}],
        "category": {
            "indicator": {
                "type": "number_of_ill_requests"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[1]]

    # one distrubtions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests",
                "distributions": ["pickup_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [label_loc_pub_martigny_bourg, 1],
        [label_loc_pub_martigny, 1],
        [label_loc_rest_martigny, 1]
    ]

    # two distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests",
                "distributions": ["pickup_location", "created_month"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', '2023-02', '2024-01'],
        [label_loc_pub_martigny_bourg, 0, 1],
        [label_loc_pub_martigny, 1, 0],
        [label_loc_rest_martigny, 1, 0]
    ]

    # reverse distrubtions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests",
                "distributions": ["created_month", "pickup_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            label_loc_pub_martigny_bourg,
            label_loc_pub_martigny,
            label_loc_rest_martigny
        ],
        ['2023-02', 0, 1, 1],
        ['2024-01', 1, 0, 0]
    ]

    # year
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests",
                "distributions": ["created_year", "pickup_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            label_loc_pub_martigny_bourg,
            label_loc_pub_martigny,
            label_loc_rest_martigny
        ],
        ['2023', 0, 1, 1],
        ['2024', 1, 0, 0]
    ]

    # type
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_ill_requests",
                "distributions": ["status", "pickup_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            label_loc_pub_martigny_bourg,
            label_loc_pub_martigny,
            label_loc_rest_martigny
        ],
        ['closed', 1, 0, 0],
        ['pending', 0, 1, 0],
        ['validated', 0, 0, 1]
    ]
