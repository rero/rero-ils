# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""DOJSON transformation for RERO MARC21 module tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime, timezone

import mock
from dojson.utils import GroupableOrderedDict

from rero_ils.modules.documents.dojson.contrib.jsontomarc21 import to_marc21


def add_created_updated(record, updated=False):
    """Adds _created and _updated to record."""
    date = datetime.now(timezone.utc)
    record['_created'] = date.isoformat()
    if updated:
        record['_updated'] = date.isoformat()
    else:
        record['_updated'] = '2027-07-07T07:07:07.000000+00:00'
    return date, record


def test_pid_to_marc21(app, marc21_record):
    """Test PID to MARC21 transformation."""
    record = {
        'pid': '12345678',
        'language': [{
            "type": "bf:Language",
            "value": "fre"
        }],
        'fiction_statement': 'fiction',
        'provisionActivity': [{
            '_text': [{
                    'language': 'default',
                    'value': 'Paris : Ed. Cornélius, 2007-'
            }],
            'place': [{
                    'country': 'fr',
                    'type': 'bf:Place'
            }],
            'startDate': 2007,
            'endDate': 2020,
            'statement': [{
                    'label': [{'value': 'Paris'}],
                    'type': 'bf:Place'
                }, {
                    'label': [{'value': 'Ed. Cornélius'}],
                    'type': 'bf:Agent'
                }, {
                    'label': [{'value': '2007-2020'}],
                    'type': 'Date'
            }],
            'type': 'bf:Publication'
        }]
    }
    date, record = add_created_updated(record, True)
    result = to_marc21.do(record)
    marc21 = deepcopy(marc21_record)
    updated = date.strftime('%Y%m%d%H%M%S.0')
    created = date.strftime('%y%m%d')
    marc21.update({
        '__order__': ('leader', '001', '005', '008', '264_1'),
        '001': '12345678',
        '005': updated,
        '008': f'{created}m20072020xx#|||||||||||||||1|fre|c',
        '264_1': {
            '__order__': ('a', 'b', 'c'),
            'a': 'Paris',
            'b': 'Ed. Cornélius',
            'c': '2007-2020'
        }
    })
    assert result == marc21
    # test fiction
    assert result['008'][33] == '1'


def test_identified_by_to_marc21(app, marc21_record):
    """Test identifiedBy to MARC21 transformation."""
    record = {
        "identifiedBy": [{
            "type": "bf:Isbn",
            "value": "9782824606835"
        }, {
            "type": "bf:Isbn",
            "value": "12345678901??",
            "status": "status",
            "qualifier": "qualifier"
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    # updated = date.strftime('%Y%m%d%H%M%S.0')
    record.update({
        '__order__': ('leader', '005', '008', '020__', '020__'),
        ''
        '020__': ({
            '__order__': ('a', ),
            'a': '9782824606835'
        }, {
            '__order__': ('z', 'q'),
            'z': '12345678901??',
            'q': 'qualifier'
        })
    })
    assert result == record


def test_title_to_marc21(app, marc21_record):
    """Test title to MARC21 transformation."""
    record = {
        'title': [{
            'type': 'bf:Title',
            'mainTitle': [{'value': 'Kunst der Farbe'}],
            'subtitle': [{'value': 'Studienausgabe'}]
        }],
        'responsibilityStatement': [
            [{'value': 'Johannes Itten'}],
            [{'value': "traduit de l'allemand par Valérie Bourgeois"}]
        ]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '2450_'),
        '2450_': {
            '__order__': ('a', 'b', 'c'),
            'a': 'Kunst der Farbe',
            'b': 'Studienausgabe',
            'c': "Johannes Itten ; traduit de l'allemand par Valérie Bourgeois"
        }
    })
    assert result == record

    record = {
        'title': [{
            'type': 'bf:Title',
            'mainTitle': [{'value': 'Statistique'}],
            'subtitle': [{
                'value': 'exercices corrigés avec rappels de cours'}],
            'part': [{
                'partNumber': [{'value': 'T. 1'}],
                'partName': [{
                    'value': 'Licence ès sciences économiques, 1ère année, '
                    'étudiants de Grandes écoles'
                    }]
            }, {
                'partNumber': [{'value': 'Section 2'}],
                'partName': [{'value': 'Grandes écoles'}]
            }]
        }],
        'responsibilityStatement': [
            [{'value': 'Edmond Berrebi'}]
        ]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '2450_'),
        '2450_': {
            '__order__': ('a', 'b', 'c', 'n', 'p', 'n', 'p'),
            'a': 'Statistique',
            'b': 'exercices corrigés avec rappels de cours',
            'c': 'Edmond Berrebi',
            'n': ('T. 1', 'Section 2'),
            'p': ('Licence ès sciences économiques, 1ère année, étudiants de '
                  'Grandes écoles',
                  'Grandes écoles')
        }
    })
    assert result == record

    record = {
        'title': [{
            'mainTitle': [{'value': 'Suisse'}],
            'type': 'bf:Title'
        }, {
            'mainTitle': [{'value': 'Schweiz'}],
            'type': 'bf:ParallelTitle'
        }, {
            'mainTitle': [{'value': 'Svizzera'}],
            'subtitle': [{'value': 'Le guide Michelin 2020'}],
            'type': 'bf:ParallelTitle'
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '2450_'),
        '2450_': {
            '__order__': ('a', 'b'),
            'a': 'Suisse',
            'b': 'Schweiz. Svizzera : Le guide Michelin 2020'
        }
    })
    assert result == record


def test_provision_activity_copyright_date_to_marc21(app, marc21_record):
    """Test provisionActivity and copyrightDate to MARC21 transformation."""
    record = {
        'fiction_statement': 'non_fiction',
        "provisionActivity": [{
            "place": [{
                "canton": "vd",
                "country": "sz",
                "type": "bf:Place"
            }],
            "startDate": 1980,
            "statement": [{
                "label": [{
                    "value": "Lausanne"
                }],
                "type": "bf:Place"
            }, {
                "label": [{
                        "value": "Institut Benjamin Constant"
                }],
                "type": "bf:Agent"
            }, {
                "label": [{
                    "value": "Genève"
                }],
                "type": "bf:Place"
            }, {
                "label": [{
                    "value": "Slatkine"
                }],
                "type": "bf:Agent"
            }, {
                "label": [{
                    "value": "Paris"
                }],
                "type": "bf:Place"
            }, {
                "label": [{
                    "value": "diff. France : H. Champion"
                }],
                "type": "bf:Agent"
            }, {
                "label": [{
                    "value": "1980-"
                }],
                "type": "Date"
            }],
            "type": "bf:Publication"
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    created = date.strftime('%y%m%d')
    record.update({
        '__order__': ('leader', '005', '008', '264_1'),
        '008': f'{created}s1980||||xx#|||||||||||||||0|||||c',
        '264_1': {
            '__order__': ('a', 'b', 'a', 'b', 'a', 'b', 'c'),
            'a': ('Lausanne', 'Genève', 'Paris'),
            'b': ('Institut Benjamin Constant', 'Slatkine',
                  'diff. France : H. Champion'),
            'c': '1980-'
        }
    })
    assert result == record

    record = {
        "provisionActivity": [{
            "endDate": 1975,
            "place": [{
                "canton": "ne",
                "country": "sz",
                "type": "bf:Place"
            }],
            "startDate": 1907,
            "statement": [{
                    "label": [{
                            "value": "La Chaux-de-Fonds"
                        }
                    ],
                    "type": "bf:Place"
                }, {
                "label": [{
                    "value": "Union Chrétienne de Jeunes Gens"
                }],
                "type": "bf:Agent"
            }, {
                "label": [{
                    "value": "1907-1975"
                }],
                "type": "Date"
            }],
            "type": "bf:Publication"
        }, {
            "statement": [{
                "label": [{
                    "value": "La Chaux-de-Fonds"
                }],
                "type": "bf:Place"
            }, {
                "label": [{
                    "value": "[successivement] Impr. C. & J. "
                             "Robert-Tissot, Imp. Robert-Tissot & Fils"
                }],
                "type": "bf:Agent"
            }],
            "type": "bf:Manufacture"
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    created = date.strftime('%y%m%d')
    record.update({
        '__order__': ('leader', '005', '008', '264_1', '264_3'),
        '008': f'{created}m19071975xx#|||||||||||||||||||||c',
        '264_1': {
            '__order__': ('a', 'b', 'c'),
            'a': 'La Chaux-de-Fonds',
            'b': 'Union Chrétienne de Jeunes Gens',
            'c': '1907-1975'
        },
        '264_3': {
            '__order__': ('a', 'b'),
            'a': 'La Chaux-de-Fonds',
            'b': '[successivement] Impr. C. & J. '
                 'Robert-Tissot, Imp. Robert-Tissot & Fils'
        }
    })
    assert result == record


def test_physical_description_to_marc21(app, marc21_record):
    """Test physical_description to MARC21 transformation."""
    record = {
        "extent": "159 p.",
        "note": [{
            "label": "fig.",
            "noteType": "otherPhysicalDetails"
        }],
        "dimensions": ["33 cm"]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '300__'),
        '300__': {
            '__order__': ('a', 'b', 'c'),
            'a': '159 p.',
            'b': 'fig.',
            'c': '33 cm'
        }
    })
    assert result == record

    record = {
        "extent": "1 DVD-vidéo",
        "duration": ["1h42"],
        "dimensions": ["In-plano", "128ᵒ"],
        "bookFormat": ["128ᵒ", "in-plano"],
        "note": [{
            "label": "accompanying material",
            "noteType": "accompanyingMaterial"
        }],
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '300__'),
        '300__': {
            '__order__': ('a', 'c', 'e'),
            'a': '1 DVD-vidéo (1h42)',
            'c': 'in-plano ; 128ᵒ',
            'e': 'accompanying material'
        }
    })
    assert result == record

    record = {
        "extent": "1 DVD-vidéo (1h42)",
        "duration": ["1h42"],
        "productionMethod": ["rdapm:1001"],
        "illustrativeContent": ["illustrations"],
        "colorContent": ["rdacc:1002"]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '300__'),
        '300__': {
            '__order__': ('a', 'b'),
            'a': '1 DVD-vidéo (1h42)',
            'b': 'blueline process ; illustrations ; black and white'
        }
    })
    assert result == record


def test_subjects_to_marc21(app, mef_agents_url, mef_concepts_url,
                            marc21_record, mef_record_with_idref_gnd,
                            mef_concept1):
    """Test subjects to MARC21 transformation."""
    record = {
        'subjects': [{
            'entity': {
                'type': 'bf:Topic',
                'source': 'rero',
                'authorized_access_point': 'Roman pour la jeunesse'
            }
        }, {
            'entity': {
                '$ref':
                    f'{mef_concepts_url}/api/concepts/idref/ent_concept_idref',
                'pid': 'ent_concept'
            }
        }, {
            'entity': {
                'date_of_birth': '1923',
                'date_of_death': '1999',
                'preferred_name': 'Fujimoto, Satoko',
                'type': 'bf:Person'
            },
            'role': ['ctb', 'aut']
        }, {
            'entity': {
                'conference': False,
                'preferred_name': 'Université de Genève',
                'type': 'bf:Organisation'
            },
            'role': ['ctb']
        }, {
            'entity': {
                '$ref': f'{mef_agents_url}/api/agents/gnd/004058518',
                'pid': '5890765',
                'type': 'bf:Organisation'
            },
            'role': ['aut']
        }, {
            'entity': {
                'conference': True,
                'conference_date': '1989',
                'numbering': '4',
                'place': 'Lausanne',
                'preferred_name': 'Congrès des animaux volants',
                'type': 'bf:Organisation'
            },
            'role': ['aut']
        }, {
            'entity': {
                'authorized_access_point':
                    'Bases de donn\u00e9esi (Voltenauer, Marc)',
                'type': 'bf:Work',
                'identifiedBy': {
                    'type': 'RERO',
                    'value': 'A001234567',
                    'source': 'rero'
                }
            }
        }, {
            'entity': {
                'authorized_access_point': 'Suisse',
                'identifiedBy': {
                    'type': 'IdRef',
                    'value': '027249654'
                },
                'source': 'rero',
                'type': 'bf:Place'
            }
        }, {
            'entity': {
                'authorized_access_point': '2500 av. J.-C.-20e siècle',
                'type': 'bf:Temporal',
                'identifiedBy': {
                    'type': 'RERO', 'value': 'A026984216'
                }
            }
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)

    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '650__', '650__', '6001_',
                      '610__', '610__', '611__', '600__', '651__', '648_7'),
        '650__': (
            GroupableOrderedDict({'a': 'Roman pour la jeunesse'}),
            GroupableOrderedDict({'a': 'Antienzymes'})
        ),
        '6001_': (
            GroupableOrderedDict({
                'a': 'Fujimoto, Satoko',
                'd': '1923 - 1999'
            })
        ),
        '600__': (
            GroupableOrderedDict({
                't': 'Bases de donnéesi (Voltenauer, Marc)',
                '2': 'rero',
                '0': 'A001234567'
            })
        ),
        '610__': (
            GroupableOrderedDict({'a': 'Université de Genève'}),
            {
                '__order__': ('a', '0', '0'),
                'a': 'Université de Genève',
                '0': ('(idref)02643136X', '(gnd)004058518')
            }
        ),
        '611__': (
            GroupableOrderedDict({
                'a': 'Congrès des animaux volants',
                'd': '1989'
            })
        ),
        '651__': (
            GroupableOrderedDict({
                'a': 'Suisse',
                '2': 'idref',
                '0': '027249654'
            })
        ),
        '648_7': (
            GroupableOrderedDict({
                'a': '2500 av. J.-C.-20e siècle',
                '2': 'rero',
                '0': 'A026984216'
            })
        )
    })
    assert result['__order__'] == record['__order__']
    assert result['650__'] == record['650__']
    assert result['600__'] == record['600__']
    assert result['6001_'] == record['6001_']
    assert result['610__'] == record['610__']
    assert result['611__'] == record['611__']
    assert result['651__'] == record['651__']
    assert result['648_7'] == record['648_7']


def test_genre_form_to_marc21(app, mef_concepts_url, marc21_record,
                              mef_concept1):
    """Test contribution to MARC21 transformation."""
    record = {
        'genreForm': [{
            'entity': {
                'type': 'bf:Topic',
                'source': 'rero',
                'authorized_access_point': 'Roman pour la jeunesse'
            }
        }, {
            'entity': {
                '$ref':
                    f'{mef_concepts_url}/api/concepts/idref/ent_concept_idref',
                'pid': 'ent_concept'
            }
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)

    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '655__', '655__'),
        '655__': (
            GroupableOrderedDict({'a': 'Roman pour la jeunesse'}),
            GroupableOrderedDict({'a': 'Antienzymes'})
        )
    })
    assert result['__order__'] == record['__order__']
    assert result['655__'] == record['655__']


def test_contribution_to_marc21(app, mef_agents_url, marc21_record,
                                mef_record_with_idref_rero,
                                mef_record_with_idref_gnd,
                                mef_record_with_idref_gnd_rero):
    """Test contribution to MARC21 transformation."""
    record = {
        'contribution': [{
            'entity': {
                'date_of_birth': '1923',
                'date_of_death': '1999',
                'preferred_name': 'Fujimoto, Satoko',
                'type': 'bf:Person'
            },
            'role': ['ctb', 'aut']
        }, {
            'entity': {
                '$ref': f'{mef_agents_url}/idref/'
                        'mef_record_with_idref_rero',
                'pid': '6627670',
                'type': 'bf:Person'
            },
            'role': ['trl']
        }, {
            'entity': {
                'conference': False,
                'preferred_name': 'Université de Genève',
                'type': 'bf:Organisation'
            },
            'role': ['ctb']
        }, {
            'entity': {
                '$ref': f'{mef_agents_url}/api/agents/gnd/'
                        'mef_record_with_idref_gnd',
                'pid': '5890765',
                'type': 'bf:Organisation'
            },
            'role': ['aut']
        }, {
            'entity': {
                'conference': True,
                'conference_date': '1989',
                'numbering': '4',
                'place': 'Lausanne',
                'preferred_name': 'Congrès des animaux volants',
                'type': 'bf:Organisation'
            },
            'role': ['aut']
        }, {
            'entity': {
                '$ref': f'{mef_agents_url}/idref/'
                        'mef_record_with_idref_gnd_rero',
                'pid': '5777972',
                'type': 'bf:Organisation'
            },
            'role': ['aut']
        }]
    }
    date, record = add_created_updated(record)
    with mock.patch(
        'rero_ils.modules.entities.remote_entities.api.'
        'RemoteEntity.get_entity',
        side_effect=[mef_record_with_idref_rero, mef_record_with_idref_gnd,
                     mef_record_with_idref_gnd_rero]
    ):
        result = to_marc21.do(record)

    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '7001_', '7001_', '710__',
                      '710__', '711__', '711__'),
        '7001_': ({
            '__order__': ('a', 'd', '4', '4'),
            'a': 'Fujimoto, Satoko',
            'd': '1923 - 1999',
            '4': ('ctb', 'aut')
        }, {
            '__order__': ('a', '4', '0', '0'),
            'a': 'Honnoré, Patrick',
            '4': 'trl',
            '0': ('(idref)072277742', '(rero)A009220673'),
        }),
        '710__': ({
            '__order__': ('a', '4'),
            'a': 'Université de Genève',
            '4': 'ctb'
        }, {
            '__order__': ('a', '4', '0', '0'),
            'a': 'Université de Genève',
            '4': 'aut',
            '0': ('(idref)02643136X', '(gnd)004058518'),
        }),
        '711__': ({
            '__order__': ('a', 'd', '4'),
            'a': 'Congrès des animaux volants',
            'd': '1989',
            '4': 'aut',
        }, {
            '__order__': ('a', '4', '0', '0', '0'),
            'a': 'Congrès ouvrier français',
            '4': 'aut',
            '0': ('(idref)03255608X', '(rero)A005462931', '(gnd)050343211')
        })
    })
    assert result['__order__'] == record['__order__']
    assert result['7001_'] == record['7001_']
    assert result['710__'] == record['710__']
    assert result['711__'] == record['711__']


def test_type_to_marc21(app, marc21_record):
    """Test type to MARC21 transformation."""
    record = {
        'type': [{
            'main_type': 'docmaintype_comic',
            'subtype': 'docsubtype_manga'
        }, {
            'main_type': 'docmaintype_map',
            'subtype': 'docsubtype_atlas'
        }]
    }
    date, record = add_created_updated(record)
    result = to_marc21.do(record)
    record = deepcopy(marc21_record)
    record.update({
        '__order__': ('leader', '005', '008', '900__', '900__'),
        '900__': ({
            '__order__': ('a', 'b'),
            'a': 'docmaintype_comic',
            'b': 'docsubtype_manga'
        }, {
            '__order__': ('a', 'b'),
            'a': 'docmaintype_map',
            'b': 'docsubtype_atlas'
        })
    })
    assert result == record


def test_holdings_items_to_marc21(app, marc21_record, document,
                                  item2_lib_sion,
                                  ebook_5, holding_lib_sion_electronic):
    """Test holding items to MARC21 transformation."""
    record = {'pid': document.pid}
    date, record = add_created_updated(record)
    result = to_marc21.do(record, with_holdings_items=False)
    marc21 = deepcopy(marc21_record)
    marc21.update({
        '__order__': ('leader', '001', '005', '008'),
        '001': document.pid
    })
    assert result == marc21

    record = {'pid': document.pid}
    _, record = add_created_updated(record)
    item2_lib_sion_save_barcode = item2_lib_sion['barcode']
    item2_lib_sion['barcode'] = '87121336'
    item2_lib_sion.update(item2_lib_sion, dbcommit=True, reindex=True)
    result = to_marc21.do(record, with_holdings_items=True)
    marc21 = deepcopy(marc21_record)
    marc21.update({
        '__order__': ('leader', '001', '005', '008', '949__'),
        '001': 'doc1',
        '949__': ({
            '__order__': ('0', '1', '2', '3', '4', '5', 'a'),
            '0': 'org2',
            '1': 'The district of Sion Libraries',
            '2': 'lib4',
            '3': 'Library of Sion',
            '4': 'loc8',
            '5': 'Sion Library Restricted Space',
            'a': '87121336'
        })
    })
    assert result == marc21

    # clean up modified data
    item2_lib_sion['barcode'] = item2_lib_sion_save_barcode
    item2_lib_sion.update(item2_lib_sion, dbcommit=True, reindex=True)

    record = {'pid': ebook_5.pid}
    _, record = add_created_updated(record)
    result = to_marc21.do(record, with_holdings_items=True)
    marc21 = deepcopy(marc21_record)
    marc21.update({
        '__order__': ('leader', '001', '005', '008', '949__'),
        '001': 'ebook5',
        '949__': {
            '__order__': ('0', '1', '2', '3', '4', '5', 'E'),
            '0': 'org2',
            '1': 'The district of Sion Libraries',
            '2': 'lib4',
            '3': 'Library of Sion',
            '4': 'loc7',
            '5': 'Sion Library Public Space',
            'E':
                'https://bm.ebibliomedia.ch/resources/5f780fc22357943b9a83ca3d'
        }
    })
    assert result == marc21
