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

"""Document filters tests."""

import mock

from rero_ils.modules.documents.views import babeltheque_enabled_view, \
    cartographic_attributes, contribution_format, doc_entity_label, \
    get_first_isbn, identified_by, main_title_text, note_general, \
    notes_except_general, part_of_format, provision_activity, \
    provision_activity_not_publication, provision_activity_original_date, \
    provision_activity_publication, title_variants, work_access_point
from rero_ils.modules.entities.models import EntityType


def test_note_general():
    """Test note general."""
    notes = [
        {
            'noteType': 'general',
            'label': 'Note general'
        },
        {
            'noteType': 'dummy',
            'label': 'dummy'
        }
    ]
    result = {'general': ['Note general']}
    assert result == note_general(notes)


def test_notes_except_general():
    """Test note except general."""
    notes = [
        {
            'noteType': 'general',
            'label': 'Note general'
        },
        {
            'noteType': 'accompanyingMaterial',
            'label': 'Accompany'
        },
        {
            'noteType': 'accompanyingMaterial',
            'label': 'Material'
        },
        {
            'noteType': 'otherPhysicalDetails',
            'label': 'Physical'
        }
    ]
    result = {
        'accompanyingMaterial': ['Accompany', 'Material'],
        'otherPhysicalDetails': ['Physical']
    }
    assert result == notes_except_general(notes)


def test_cartographic_attributes():
    """Test cartographic attributes."""
    attributes = [
        {
            'projection': 'Projection',
            'coordinates': {
                'label': 'coordinate label'
            }
        },
        {
            'projection': 'Projection 2'
        },
        {
            'coordinates': {
                'label': 'coordinate label 2'
            }
        },
        {
            'dummy': 'dummy'
        }
    ]
    result = [
        {
            'projection': 'Projection',
            'coordinates': {
                'label': 'coordinate label'
            }
        },
        {
            'projection': 'Projection 2'
        },
        {
            'coordinates': {
                'label': 'coordinate label 2'
            }
        }
    ]
    assert result == cartographic_attributes(attributes)


def test_provision_activity():
    """Test preprocess provision activity."""
    provisions = [
        {
            '_text': [
                {
                    'language': 'default',
                    'value': 'Paris : Ed. de Minuit, 1988'
                }
            ],
            'place': [{'country': 'fr', 'type': 'bf:Place'}],
            'startDate': 1988,
            'statement': [
                {'label': [{'value': 'Paris'}], 'type': 'bf:Place'},
                {'label': [{'value': 'Ed. de Minuit'}], 'type': 'bf:Agent'},
                {'label': [{'value': '1988'}], 'type': 'Date'}
            ],
            'type': 'bf:Publication'
        },
        {
            '_text': [
                {
                    'language': 'default',
                    'value': 'Martigny : Alex Morgan, 2010'
                }
            ],
            'startDate': 1998,
            'statement': [
                {'label': [{'value': 'Martigny'}], 'type': 'bf:Place'},
                {'label': [{'value': 'Alex Morgan'}], 'type': 'bf:Agent'},
                {'label': [{'value': '2010'}], 'type': 'Date'}
            ],
            'type': 'bf:Distribution'
        },
        {
            '_text': [
                {
                    'language': 'default',
                    'value': 'Will Edwards, 2010 ; Paris ; Martigny'
                }
            ],
            'startDate': 1990,
            'statement': [
                {'label': [{'value': 'Will Edwards'}], 'type': 'bf:Agent'},
                {'label': [{'value': '2010'}], 'type': 'Date'},
                {'label': [{'value': 'Paris'}], 'type': 'bf:Place'},
                {'label': [{'value': 'Martigny'}], 'type': 'bf:Place'}
            ],
            'type': 'bf:Distribution'
        },
        {
            '_text': [{'language': 'default', 'value': ''}],
            'original_date': 2010,
            'place': [{'country': 'xx', 'type': 'bf:Place'}],
            'startDate': 1989,
            'type': 'bf:Manufacture'
        }
    ]
    result = {
        'bf:Publication': [
            {'language': 'default', 'value': 'Paris : Ed. de Minuit, 1988'}
        ],
        'bf:Distribution': [
            {'language': 'default', 'value': 'Martigny : Alex Morgan, 2010'},
            {
                'language': 'default',
                'value': 'Will Edwards, 2010 ; Paris ; Martigny'
            }
        ]
    }
    assert result == provision_activity(provisions)


def test_provision_activity_publication():
    """Test extract only publication on provision activity."""
    provisions = {
        'bf:Publication': [
            {'language': 'default', 'value': 'Paris : Ed. de Minuit, 1988'}
        ],
        'bf:Distribution': [
            {'language': 'default', 'value': 'Martigny : Alex Morgan, 2010'},
            {
                'language': 'default',
                'value': 'Will Edwards, 2010 ; Paris ; Martigny'
            }
        ]
    }
    result = {
        'bf:Publication': [
            {'language': 'default', 'value': 'Paris : Ed. de Minuit, 1988'}
        ]
    }
    assert result == provision_activity_publication(provisions)


def test_provision_activity_not_publication():
    """Test extract all provision activity except publication."""
    provisions = {
        'bf:Publication': [
            {'language': 'default', 'value': 'Paris : Ed. de Minuit, 1988'}
        ],
        'bf:Distribution': [
            {'language': 'default', 'value': 'Martigny : Alex Morgan, 2010'},
            {
                'language': 'default',
                'value': 'Will Edwards, 2010 ; Paris ; Martigny'
            }
        ]
    }
    result = {
        'bf:Distribution': [
            {'language': 'default', 'value': 'Martigny : Alex Morgan, 2010'},
            {
                'language': 'default',
                'value': 'Will Edwards, 2010 ; Paris ; Martigny'
            }
        ]
    }
    assert result == provision_activity_not_publication(provisions)


def test_provision_activity_original_date():
    """Test provision activity."""
    activity = [
        {
            'original_date': '2021'
        },
        {
            'date': '2021-07-23'
        }
    ]
    result = ['2021']
    assert result == provision_activity_original_date(activity)


def test_title_variants():
    """Test title variants."""
    titles = [
        {
            'type': 'bf:Title',
            'mainTitle': [{
                'value': 'Title'
            }]
        },
        {
            'type': 'bf:VariantTitle',
            'mainTitle': [{
                'value': 'Variant title 1'
            }],
            'part': [
                {
                    'partName': [{'value': 'part1'}],
                    'partNumber': [{'value': 'number1'}],
                },
                {
                    'partNumber': [{'value': 'number2'}],
                    'partName': [{'value': 'part2'}]
                }
            ]
        },
        {
            'type': 'bf:VariantTitle',
            'mainTitle': [{
                'value': 'Variant title 2'
            }],
            'subtitle': [{
                'value': 'Variant 2 sub'
            }]
        },
        {
            'type': 'bf:ParallelTitle',
            'mainTitle': [{
                'value': 'Parallel title'
            }],
            'subtitle': [{
                'value': 'sub parallel'
            }]
        }
    ]
    result = {
        'bf:VariantTitle':
        [
            'Variant title 1. number1, part1. number2, part2',
            'Variant title 2 : Variant 2 sub'
        ],
        'bf:ParallelTitle': ['Parallel title : sub parallel']
    }

    assert result == title_variants(titles)


def test_work_access_point():
    """Test work access point process."""
    wap = [
        {
            'part': [
                {
                    'partName': 'part section title',
                    'partNumber': 'part section designation'
                }
            ],
            'creator': {
                'type': 'bf:Person',
                'qualifier': 'physicien',
                'numeration': 'XX',
                'date_of_birth': '1955',
                'date_of_death': '2012',
                'preferred_name':
                'Müller, Hans',
                'fuller_form_of_name':
                'Müller, Hans Peter'
            },
            'title': 'Müller, Hans (Title)',
            'language': 'fre',
            'date_of_work': '2000',
            'key_for_music': 'key music',
            'form_subdivision': ['Form sub.'],
            'miscellaneous_information': 'Miscellaneous info',
            'arranged_statement_for_music': 'arranged stat',
            'medium_of_performance_for_music': ['medium perf']
        },
        {
            'part': [
                {
                    'partName': 'Title',
                    'partNumber': 'part designation'
                }],
            'creator': {
                'type': 'bf:Organisation',
                'place': 'Lausanne',
                'numbering': '4',
                'conference': False,
                'preferred_name': 'Corp body Name',
                'conference_date': '1990',
                'subordinate_unit': ['Office 1', 'Office 2']
            },
            'title': 'Corp Title',
            'language': 'fre',
            'date_of_work': '1980',
            'key_for_music': 'Corp Key music',
            'form_subdivision': ['Form sub 1', 'Form sub 2'],
            'miscellaneous_information': 'miscellaneous info',
            'arranged_statement_for_music': 'Copr Arranged stat',
            'medium_of_performance_for_music': [
                'Corp Medium perf  1',
                'Corp Medium perf  2'
            ]
        },
        {
            'creator': {
                'type': 'bf:Person',
                'qualifier': 'pianiste',
                'date_of_birth': '1980',
                'preferred_name': 'Hans, Peter'
            },
            'title': 'Work title'
        },
        {
            'part': [
                {
                    'partNumber': 'part number'
                }
            ],
            'creator': {
                'type': 'bf:Person',
                'qualifier': 'pianiste'
            },
            'title': 'title with part'
        }
    ]
    results = [
        'Müller, Hans, XX, physicien, 1955-2012. Müller, Hans (Title). '
        'part section designation. part section title. Miscellaneous info. '
        'lang_fre. medium perf. key music. arranged stat. 2000.',
        'Corp body Name. Office 1. Office 2. (4 : 1990 : Lausanne) '
        'Corp Title. part designation. Title. miscellaneous info. '
        'lang_fre. Corp Medium perf  1. Corp Medium perf  2. '
        'Corp Key music. Copr Arranged stat. 1980.',
        'Hans, Peter, 1980. pianiste. Work title.',
        'pianiste. title with part. part number.'
    ]
    assert results == work_access_point(wap)


def test_contribution_format(db, entity_organisation):
    """Test contribution format."""
    entity = entity_organisation
    contributions = [{
        'entity': {
            'authorized_access_point': 'author_def',
            'authorized_access_point_fr': 'author_fr'
        }
    }]

    # ---- Textual contribution
    # With english language
    link_part = '/global/search/documents?q=' \
                'contribution.entity.authorized_access_point_en%3A' \
                '%22author_def%22'
    assert link_part in contribution_format(contributions, 'en', 'global')

    # With french language
    link_part = '/global/search/documents?q=' \
                'contribution.entity.authorized_access_point_fr%3A' \
                '%22author_fr%22'
    assert link_part in contribution_format(contributions, 'fr', 'global')

    # ---- Remote contribution
    contributions = [{
        'entity': {'pid': entity.pid}
    }]
    link_part = f'/global/search/documents?q=' \
                f'contribution.entity.pids.{entity.resource_type}%3A' \
                f'{entity.pid}'
    assert link_part in contribution_format(contributions, 'en', 'global')


def test_identifiedby_format():
    """Test identifiedBy format."""
    identifiedby = [
        {
            'type': 'bf:Local',
            'source': 'RERO',
            'value': 'R008745599'
        }, {
            'note':	'Lorem ipsun dolor',
            'qualifier': 'Qualifier',
            'status': 'cancelled',
            'type': 'bf:Isbn',
            'value': '9782844267788'
        }, {
            'note':	'Lorem ipsun dolor',
            'type': 'bf:Local',
            'source': 'BNF',
            'value': 'FRBNF452959040000002'
        }, {
            'type': 'uri',
            'value': 'http://catalogue.bnf.fr/ark:/12148/cb45295904f'
        }
    ]
    results = [
        {
            'details': '',
            'type': 'RERO',
            'value': 'R008745599'
        },
        {
            'details': 'Qualifier, cancelled, Lorem ipsun dolor',
            'type': 'bf:Isbn',
            'value': '9782844267788'
        },
        {
            'details': 'Lorem ipsun dolor',
            'type': 'BNF',
            'value': 'FRBNF452959040000002'
        },
        {
            'details': '',
            'type': 'uri',
            'value': 'http://catalogue.bnf.fr/ark:/12148/cb45295904f'
        }
    ]
    assert results == identified_by(identifiedby)


def test_part_of_format(
    document_with_issn,
    document2_with_issn,
    document_sion_items
):
    """Test 'part of' format."""
    # Label Series with numbering
    part_of = {
        "document": {
          "$ref": "https://bib.rero.ch/api/documents/doc5"
        },
        "numbering": [
            {
                "year": "1818",
                "volume": 2704,
                "issue": "1",
                "pages": "55"
            }
        ]
    }
    result = {
        "document_pid": "doc5",
        "label": "Series",
        "numbering": [
            "1818, vol. 2704, nr. 1, p. 55"
        ],
        "title": "Manuales del Africa espa\u00f1ola"
    }
    assert result == part_of_format(part_of)
    # Label Journal with numbering
    part_of = {
        "document": {
          "$ref": "https://bib.rero.ch/api/documents/doc6"
        },
        "numbering": [
            {
                "year": "1818",
                "volume": 2704,
                "issue": "1",
                "pages": "55"
            }
        ]
    }
    result = {
        "document_pid": "doc6",
        "label": "Journal",
        "numbering": [
            "1818, vol. 2704, nr. 1, p. 55"
        ],
        "title": "Nota bene"
    }
    assert result == part_of_format(part_of)
    # Label Published in without numbering
    part_of = {
        "document": {
          "$ref": "https://bib.rero.ch/api/documents/doc3"
        }
    }
    result = {
        "document_pid": "doc3",
        "label": "Published in",
        "title": "La reine Berthe et son fils"
    }
    assert result == part_of_format(part_of)


def test_main_title_text():
    """Test extract only main title."""
    title = [
        {
            "mainTitle": [{"value": "J. Am. Med. Assoc."}],
            "type": "bf:AbbreviatedTitle"
        },
        {
            "mainTitle": [{"value": "J Am Med Assoc"}],
            "type": "bf:KeyTitle"
        },
        {
            "_text": "Journal of the American medical association",
            "mainTitle": [{
                "value": "Journal of the American medical association"}],
            "type": "bf:Title"
        }
    ]
    extract = main_title_text(title)
    assert len(extract) == 1
    assert extract[0].get('_text') is not None


def test_doc_entity_label_filter(entity_person, local_entity_person):
    """Test entity label filter."""

    # Remote entity
    remote_pid = entity_person['idref']['pid']
    data = {
        'entity': {
            '$ref': f'https://mef.rero.ch/api/concepts/idref/{remote_pid}',
            'pid': remote_pid
        }
    }
    entity_type, value, label = doc_entity_label(data['entity'], 'fr')
    assert 'remote' == entity_type
    assert 'ent_pers' == value
    assert 'Loy, Georg, 1885-19..' == label

    # Local entity
    pid = local_entity_person['pid']
    data = {
        'entity': {
            '$ref': f'https://bib.rero.ch/api/local_entities/{pid}'
        }
    }
    entity_type, value, label = doc_entity_label(data['entity'], 'fr')
    assert 'local' == entity_type
    assert 'locent_pers' == value
    assert 'Loy, Georg (1881-1968)' == label

    entity_type, value, label = doc_entity_label(data['entity'], 'en')
    assert 'local' == entity_type
    assert 'locent_pers' == value
    assert 'Loy, Georg (1881-1968)' == label

    # Textual
    data = {
        'entity': {
            'authorized_access_point': 'subject topic'
        }
    }
    entity_type, value, label = doc_entity_label(data['entity'], None)
    assert 'textual' == entity_type
    assert 'subject topic' == value
    assert 'subject topic' == label

    entity_type, value, label = doc_entity_label(data['entity'], 'fr')
    assert 'textual' == entity_type
    assert 'subject topic' == value
    assert 'subject topic' == label

    # Textual with subdivision
    data['entity']['subdivisions'] = [
        {
            'entity': {
                'authorized_access_point': 'Sub 1',
                'type': EntityType.TOPIC
            }
        },
        {
            'entity': {
                'authorized_access_point': 'Sub 2',
                'type': EntityType.TOPIC
            }
        }
    ]
    entity_type, value, label = doc_entity_label(data['entity'], 'fr')
    assert 'textual' == entity_type
    assert 'subject topic' == value
    assert 'subject topic - Sub 1 - Sub 2' == label


def test_babeltheque_enabled_view():
    """Check enabled view for babeltheque."""
    class CurrentApp:
        """Current app mock."""
        config = {'RERO_ILS_APP_BABELTHEQUE_ENABLED_VIEWS': ['global']}
    with mock.patch(
            'rero_ils.modules.documents.views.current_app', CurrentApp):
        assert babeltheque_enabled_view('global')
        assert not babeltheque_enabled_view('foo')


def test_get_first_isbn():
    """Get the first isbn on identifiedBy field."""
    record = {'identifiedBy': [
        {'type': 'bf:Isbn', 'value': '9782501053006'},
        {'type': 'bf:Isbn', 'value': '9782501033671'}
    ]}
    assert '9782501053006' == get_first_isbn(record)
    record = {'identifiedBy': []}
    assert None is get_first_isbn(record)
