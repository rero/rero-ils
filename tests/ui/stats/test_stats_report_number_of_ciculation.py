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

"""Stats Report tests circulation indicators."""

from datetime import datetime

import mock
from invenio_search import current_search_client as es

from rero_ils.modules.stats.api.report import StatsReport


def test_stats_report_circulation_trigger(
        org_martigny, lib_martigny, lib_martigny_bourg, loc_public_martigny,
        loc_public_martigny_bourg):
    """Test the circulation indicuators."""
    # fixtures
    for trigger in [
        'checkin', 'checkout', 'extend', 'request', 'validate_request'
    ]:
        es.index(index='operation_logs-2020', id='1', body={
            "date": "2023-01-01",
            "loan": {
                "trigger": trigger,
                "item": {
                    "document": {
                        "type": "docsubtype_other_book"
                    },
                    "library_pid": lib_martigny.pid,
                    "holding": {
                        "location_name": loc_public_martigny["name"]
                    }
                },
                "transaction_location": {"pid": loc_public_martigny.pid},
                "transaction_channel": "sip2",
                "patron": {
                    "age": 13,
                    "type": "Usager.ère moins de 14 ans",
                    "postal_code": "1920"
                }
            },
            "record": {
                "type": "loan",
            }
        }, refresh=True)
        es.index(index='operation_logs-2020', id='2', body={
            "date": "2023-01-01",
            "loan": {
                "trigger": trigger,
                "item": {
                    "document": {
                        "type": "docsubtype_other_book"
                    },
                    "library_pid": lib_martigny.pid,
                    "holding": {
                        "location_name": loc_public_martigny["name"]
                    }
                },
                "transaction_location": {"pid": loc_public_martigny_bourg.pid},
                "transaction_channel": "sip2",
                "patron": {
                    "age": 13,
                    "type": "Usager.ère moins de 14 ans",
                    "postal_code": "1920"
                }
            },
            "record": {
                "type": "loan",
            }
        }, refresh=True)

        cfg = {
            "library": {
                "$ref": "https://bib.rero.ch/api/libraries/lib1"
            },
            "is_active": True,
            "category": {
                "indicator": {
                    "type": f"number_of_{trigger}s"
                }
            }
        }
        assert StatsReport(cfg).collect() == [[2]]
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
                    "type": f"number_of_{trigger}s"
                }
            }
        }
        assert StatsReport(cfg).collect() == [[1]]


def test_stats_report_number_of_checkins(
        org_martigny, org_sion, lib_martigny, lib_martigny_bourg,
        lib_sion, loc_public_martigny,
        loc_public_martigny_bourg, loc_public_sion):
    """Test the number of circulation checkins operations."""
    label_loc_pub_martigny = f'{lib_martigny["name"]} / '\
        f'{loc_public_martigny["name"]} ({loc_public_martigny.pid})'
    label_loc_pub_martigny_bourg = f'{lib_martigny_bourg["name"]} / '\
        f'{loc_public_martigny_bourg["name"]} '\
        f'({loc_public_martigny_bourg.pid})'

    # fixtures
    es.index(index='operation_logs-2020', id='1', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "checkin",
            "item": {
                "document": {
                    "type": "docsubtype_other_book"
                },
                "library_pid": lib_martigny.pid,
                "holding": {
                    "location_name": loc_public_martigny["name"]
                }
            },
            "transaction_location": {"pid": loc_public_martigny.pid},
            "transaction_channel": "sip2",
            "patron": {
                "age": 13,
                "type": "Usager.ère moins de 14 ans",
                "postal_code": "1920"
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    es.index(index='operation_logs-2020', id='2', body={
        "date": "2024-01-01",
        "loan": {
            "trigger": "checkin",
            "item": {
                "document": {
                    "type": "ebook"
                },
                "library_pid": lib_martigny_bourg.pid,
                "holding": {
                    "location_name": loc_public_martigny_bourg["name"]
                }
            },
            "transaction_location": {"pid": loc_public_martigny_bourg.pid},
            "transaction_channel": "system",
            "patron": {
                "age": 30,
                "type": "Usager.ère plus de 18 ans",
                "postal_code": "1930"
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    es.index(index='operation_logs-2020', id='3', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "checkin",
            "item": {
                "document": {
                    "type": "ebook"
                },
                "library_pid": lib_sion.pid
            },
            "transaction_location": {"pid": loc_public_sion.pid},
            "transaction_channel": "sip2",
            "patron": {
                "age": 13,
                "type": "Usager.ère moins de 14 ans",
                "postal_code": "1920"
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    es.index(index='operation_logs-2020', id='4', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "checkin",
            "item": {
                "document": {
                    "type": "docsubtype_other_book"
                },
                "library_pid": lib_martigny_bourg.pid

            },
            "transaction_location": {"pid": loc_public_martigny_bourg.pid},
            "transaction_channel": "sip2",
            "patron": {
                "age": 13,
                "type": "Usager.ère moins de 14 ans",
                "postal_code": "1920"
            }
        },
        "record": {
          "type": "item",
        }
    }, refresh=True)

    es.index(index='operation_logs-2020', id='5', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "checkout",
            "item": {
                "document": {
                    "type": "docsubtype_other_book"
                },
                "library_pid": lib_martigny_bourg.pid
            },
            "transaction_location": {"pid": loc_public_martigny_bourg.pid},
            "transaction_channel": "sip2",
            "patron": {
                "age": 10,
                "type": "Usager.ère moins de 14 ans",
                "postal_code": "1920"
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    # no distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins"
            }
        }
    }
    assert StatsReport(cfg).collect() == [[2]]

    # limit by period
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "period": "year"
            }
        }
    }
    with mock.patch(
        'rero_ils.modules.stats.api.report.datetime'
    ) as mock_datetime:
        mock_datetime.now.return_value = datetime(year=2024, month=1, day=1)
        assert StatsReport(cfg).collect() == [[1]]

    # one distrubtions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["transaction_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [label_loc_pub_martigny_bourg, 1],
        [label_loc_pub_martigny, 1]
    ]
    # two distributions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["transaction_location", "transaction_month"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['', '2023-01', '2024-01'],
        [label_loc_pub_martigny_bourg, 0, 1],
        [label_loc_pub_martigny, 1, 0]
    ]

    # reverse distrubtions
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["transaction_month", "transaction_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            label_loc_pub_martigny_bourg,
            label_loc_pub_martigny
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
                "type": "number_of_checkins",
                "distributions": ["transaction_year", "transaction_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [
            '',
            label_loc_pub_martigny_bourg,
            label_loc_pub_martigny
        ],
        ['2023', 0, 1],
        ['2024', 1, 0]
    ]

    # patron type
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["patron_type"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['Usager.ère moins de 14 ans', 1],
        ['Usager.ère plus de 18 ans', 1]
    ]

    # patron age
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["patron_age"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [13, 1],
        [30, 1]
    ]

    # postal code
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["patron_postal_code"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['1920', 1],
        ['1930', 1]
    ]

    # patron type
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["patron_type"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['Usager.ère moins de 14 ans', 1],
        ['Usager.ère plus de 18 ans', 1]
    ]

    # patron type
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["document_type"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['docsubtype_other_book', 1],
        ['ebook', 1]
    ]

    # transaction channel
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["transaction_channel"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        ['sip2', 1],
        ['system', 1]
    ]

    # owning library
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["owning_library"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [f'{lib_martigny_bourg.get("name")} ({lib_martigny_bourg.pid})', 1],
        [f'{lib_martigny.get("name")} ({lib_martigny.pid})', 1]
    ]

    # owning location
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_checkins",
                "distributions": ["owning_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [loc_public_martigny_bourg['name'], 1],
        [loc_public_martigny['name'], 1]
    ]


def test_stats_report_number_of_requests(
        lib_martigny, lib_martigny_bourg, loc_public_martigny,
        loc_public_martigny_bourg):
    """Test the number of circulation checkins operations."""
    label_loc_pub_martigny = f'{lib_martigny["name"]} / '\
        f'{loc_public_martigny["name"]} ({loc_public_martigny.pid})'
    label_loc_pub_martigny_bourg = f'{lib_martigny_bourg["name"]} / '\
        f'{loc_public_martigny_bourg["name"]} '\
        f'({loc_public_martigny_bourg.pid})'

    # fixtures
    es.index(index='operation_logs-2020', id='1', body={
        "date": "2023-01-01",
        "loan": {
            "trigger": "request",
            "item": {
                "document": {
                    "type": "docsubtype_other_book"
                },
                "library_pid": lib_martigny.pid,
                "holding": {
                    "location_name": loc_public_martigny["name"]
                }
            },
            "transaction_location": {"pid": loc_public_martigny.pid},
            "pickup_location": {"pid": loc_public_martigny.pid},
            "transaction_channel": "sip2",
            "patron": {
                "age": 13,
                "type": "Usager.ère moins de 14 ans",
                "postal_code": "1920"
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    es.index(index='operation_logs-2020', id='2', body={
        "date": "2024-01-01",
        "loan": {
            "trigger": "request",
            "item": {
                "document": {
                    "type": "ebook"
                },
                "library_pid": lib_martigny_bourg.pid,
                "holding": {
                    "location_name": loc_public_martigny_bourg["name"]
                }
            },
            "transaction_location": {"pid": loc_public_martigny_bourg.pid},
            "pickup_location": {"pid": loc_public_martigny_bourg.pid},
            "transaction_channel": "system",
            "patron": {
                "age": 30,
                "type": "Usager.ère plus de 18 ans",
                "postal_code": "1930"
            }
        },
        "record": {
          "type": "loan",
        }
    }, refresh=True)

    # pickup location
    cfg = {
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        "is_active": True,
        "category": {
            "indicator": {
                "type": "number_of_requests",
                "distributions": ["pickup_location"]
            }
        }
    }
    assert StatsReport(cfg).collect() == [
        [label_loc_pub_martigny_bourg, 1],
        [label_loc_pub_martigny, 1]
    ]
