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

"""Stats Report tests for number of patrons."""

import hashlib
from datetime import datetime

import mock
from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_number_of_patrons(
        db, org_martigny, lib_martigny, org_sion, lib_martigny_bourg,
        patron_type_children_martigny, patron_type_adults_martigny,
        patron_type_grown_sion, loc_public_martigny,
        loc_public_martigny_bourg,
        patron_martigny_data,
        patron2_martigny_data, patron_sion_data, roles
):
    """Test the number of patrons and active patrons."""
    def patch_creation_date(patron, date):
        patron.model.created = date
        db.session.merge(patron.model)
        patron.reindex()

    # no data
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[0]]

    from rero_ils.modules.patrons.utils import create_patron_from_data

    patron_martigny = create_patron_from_data(
        data={k: v for k, v in patron_martigny_data.items() if k != 'pid'},
        dbcommit=True,
        reindex=True)
    patron2_martigny = create_patron_from_data(
        data={k: v for k, v in patron2_martigny_data.items() if k != 'pid'},
        dbcommit=True,
        reindex=True)
    patron_sion = create_patron_from_data(
        data={k: v for k, v in patron_sion_data.items() if k != 'pid'},
        dbcommit=True,
        reindex=True)
    date = datetime(year=2023, month=11, day=1)
    patch_creation_date(patron_martigny, date)
    patch_creation_date(patron2_martigny, date)
    patch_creation_date(patron_sion, date)
    es.indices.refresh(index='patrons')

    # no distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[2]]

    # gender
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "distributions": ["gender"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['female', 1],
        ['male', 1]
    ]
    # birth year
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "distributions": ["birth_year"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['1947', 1],
        ['1967', 1]
    ]
    # patron type
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "distributions": ["type"]
            }
        }
    }
    label_ptrn_type_children = f'{patron_type_children_martigny["name"]} '\
        f'({patron_type_children_martigny.pid})'
    label_ptrn_type_adult = f'{patron_type_adults_martigny["name"]} '\
        f'({patron_type_adults_martigny.pid})'
    assert StatsReport(cfg).collect() == [
        [label_ptrn_type_adult, 1],
        [label_ptrn_type_children, 1]
    ]
    # postal code
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "distributions": ["postal_code"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['1920', 2]
    ]
    # role
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "distributions": ["role"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['patron', 2]
    ]
    # gender month
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "distributions": ["gender", "created_month"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', '2023-11'],
        ['female', 1],
        ['male', 1]
    ]

    # gender year
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_patrons",
                "period": "year",
                "distributions": ["created_year", "gender"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
       ['', 'female', 'male'],
       ['2023', 1, 1]
    ]

    es.index(index='operation_logs-2020', id='1', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "checkin",
            "patron": {
                "pid": patron_martigny.pid,
                "hashed_pid": hashlib.md5(
                    patron_martigny.pid.encode()).hexdigest()
            },
            "item": {
                "library_pid": lib_martigny.pid
            },
            "transaction_location": {
                "pid": loc_public_martigny.pid
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    es.index(index='operation_logs-2020', id='2', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "checkin",
            "patron": {
                "pid": patron2_martigny.pid,
                "hashed_pid": hashlib.md5(
                    patron2_martigny.pid.encode()).hexdigest()
            },
            "item": {
                "library_pid": lib_martigny_bourg.pid
            },
            "transaction_location": {
                "pid": loc_public_martigny_bourg.pid
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    # active patrons
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_active_patrons",
                "period": "year",
            }
        }
    }
    with mock.patch(
        'rero_ils.modules.stats.api.report.datetime'
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(year=2024, month=1, day=1)

        assert StatsReport(cfg).collect() == [[2]]

    # active patrons
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
                "type": "number_of_active_patrons",
                "period": "year",
            }
        }
    }
    with mock.patch(
        'rero_ils.modules.stats.api.report.datetime'
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(year=2024, month=1, day=1)

        assert StatsReport(cfg).collect() == [[1]]
