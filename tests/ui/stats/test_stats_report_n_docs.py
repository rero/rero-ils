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

"""Stats Report tests for number of documents."""

from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_documents(
        org_martigny, org_sion, lib_martigny, lib_martigny_bourg,
        lib_sion):
    """Test the number of documents."""
    # fixtures
    es.index(index='documents', id='1', body={
        '_created': "2023-02-01",
        'adminMetadata': {'source': 'foo'},
        'holdings': [{
            'organisation': {
                'organisation_pid': org_martigny.pid,
                'library_pid': lib_martigny.pid
            }
        }
        ]
    })
    es.index(index='documents', id='2', body={
        '_created': "2024-01-01",
        'holdings': [{
            'organisation': {
                'organisation_pid': org_martigny.pid,
                'library_pid': lib_martigny_bourg.pid
            }
        }, {
            'organisation': {
                'organisation_pid': org_sion.pid,
                'library_pid': lib_sion.pid
            }
        }
        ]
    })
    es.index(index='documents', id='3', body={
        '_created': "2024-01-01",
        'holdings': [{
            'organisation': {
                'organisation_pid': org_sion.pid,
                'library_pid': lib_sion.pid
            }
        }
        ]
    })
    es.indices.refresh(index='documents')

    # no distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_documents"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[2]]

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
                "type": "number_of_documents"
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
                "type": "number_of_documents",
                "distributions": ["owning_library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1]
    ]

    # two distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_documents",
                "distributions": ["owning_library", "created_month"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', '2023-02', '2024-01'],
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
                "type": "number_of_documents",
                "distributions": ["created_month", "owning_library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['2023-02', 0, 1],
        ['2024-01', 1, 0]
    ]

    # by year
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_documents",
                "distributions": ["created_year", "owning_library"]
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

    # imported
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_documents",
                "distributions": ["owning_library", "imported"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', 'imported', 'not imported'],
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 0, 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1, 0]
    ]

    # reverse imported
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_documents",
                "distributions": ["imported", "owning_library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})',
            f'{lib_martigny.get("name")} ({lib_martigny.pid})'
        ],
        ['imported', 0, 1],
        ['not imported', 1, 0]
    ]
