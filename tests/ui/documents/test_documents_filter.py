# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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


from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.views import authors_format, get_note, \
    identifiedby_format, language_format, note_format, part_of_format, \
    series_format
from rero_ils.modules.items.models import ItemNoteTypes


def test_get_note(item_lib_martigny):
    """Test get_note function."""
    assert get_note(item_lib_martigny, ItemNoteTypes.STAFF) is not None
    assert get_note(item_lib_martigny, ItemNoteTypes.CHECKIN) is None


def test_authors_format(db, document_data):
    """Test authors format."""
    result = 'Vincent, Sophie'
    doc = Document.create(document_data, delete_pid=True)
    assert result == authors_format(doc.pid, 'en', 'global')


def test_series_format():
    """Test series format."""
    serie = {
        "seriesTitle": [
            {
                "value": "Materialis Programm"
            }
        ],
        "seriesEnumeration": [
            {
                "value": "MP 31"
            }
        ],
        "subseriesStatement": [
            {
                "subseriesTitle": [
                    {
                        "value": "Kollektion: Philosophie"
                    }
                ]
            }
        ]
    }
    result = [{
        'language': 'default',
        'value': 'Materialis Programm; MP 31. Kollektion: Philosophie'
    }]
    assert result == series_format(serie)


def test_language_format_format(app):
    """Test language format."""
    language = [
        {
            'type': 'bf:Language',
            'value': 'ger'
        }, {
            'type': 'bf:Language',
            'value': 'fre'
        }
    ]
    results = 'German, French'
    assert results == language_format(language, 'en')

    language = 'fre'
    results = 'French'
    assert results == language_format(language, 'en')


def test_identifiedby_format():
    """Test identifiedBy format."""
    identifiedby = [
        {
            'type': 'bf:Local',
            'source': 'RERO',
            'value': 'R008745599'
        }, {
            'type': 'bf:Isbn',
            'value': '9782844267788'
        }, {
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
            'type': 'Isbn', 'value': '9782844267788'},
        {
            'type': 'uri',
            'value': 'http://catalogue.bnf.fr/ark:/12148/cb45295904f'}
    ]
    assert results == identifiedby_format(identifiedby)


def test_note_format():
    """Test note format."""
    notes = [
      {
        "noteType": "accompanyingMaterial",
        "label": "1 livret"
      },
      {
        "noteType": "general",
        "label": "Inhalt: Mrs Dalloway ; Orlando ; The waves"
      },
      {
        "noteType": "otherPhysicalDetails",
        "label": "ill."
      }
    ]
    result = {
        "accompanyingMaterial":
            [
                "1 livret"
            ],
        "general":
            [
                "Inhalt: Mrs Dalloway ; Orlando ; The waves"
            ],
        "otherPhysicalDetails":
            [
                "ill."
            ]
        }
    assert result == note_format(notes)


def test_part_of_format(
    document_with_issn,
    document2_with_issn,
    document_sion_items
):
    """Test 'part of' format."""
    # Label Series with numbering
    part_of = {
        "document": {
          "$ref": "https://ils.rero.ch/api/documents/doc5"
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
          "$ref": "https://ils.rero.ch/api/documents/doc6"
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
          "$ref": "https://ils.rero.ch/api/documents/doc3"
        }
    }
    result = {
        "document_pid": "doc3",
        "label": "Published in",
        "title": "La reine Berthe et son fils"
    }
    assert result == part_of_format(part_of)
