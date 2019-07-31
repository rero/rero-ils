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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Document JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(document_schema, document_data_tmp):
    """Test required for jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        validate({}, document_schema)


def test_pid(document_schema, document_data_tmp):
    """Test pid for jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['pid'] = 25
        validate(document_data_tmp, document_schema)


def test_title(document_schema, document_data_tmp):
    """Test title for jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['title'] = 2
        validate(document_data_tmp, document_schema)


def test_titlesProper(document_schema, document_data_tmp):
    """Test titlesProper for jsonschemas."""
    document_data_tmp['titlesProper'] = ['RERO21 pour les nuls']

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['titlesProper'] = 'string is a bad type'
        validate(document_data_tmp, document_schema)


def test_type(document_schema, document_data_tmp):
    """Test type for document jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['type'] = 2
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['type'] = 'CD-ROM'
        validate(document_data_tmp, document_schema)


def test_is_part_of(document_schema, document_data_tmp):
    """Test type for document jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['is_part_of'] = 2
        validate(document_data_tmp, document_schema)


def test_languages(document_schema, document_data_tmp):
    """Test languages for jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['language'][0]['value'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['language'][0]['value'] = ['gre']
        validate(document_data_tmp, document_schema)


def test_translatedFrom(document_schema, document_data_tmp):
    """Test translatedFrom for jsonschemas."""
    document_data_tmp['translatedFrom'] = ['eng']

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['translatedFrom'] = [2]
        validate(document_data_tmp, document_schema)


def test_authors(document_schema, document_data_tmp):
    """Test authors for jsonschemas."""
    document_data_tmp['authors'] = [
        {
            'name': 'Dumont, Jean',
            'type': 'person',
            'date': '1954 -',
            'qualifier': 'Développeur'
        },
        {
            'type': 'organisation',
            'name': 'RERO'
        }
    ]

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['authors'][0]['name'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['authors'][0]['type'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['authors'][0]['date'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['authors'][0]['qualifier'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['authors'][1]['type'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['authors'][1]['name'] = [2]
        validate(document_data_tmp, document_schema)


def test_publishers(document_schema, document_data_tmp):
    """Test publishers for jsonschemas."""
    document_data_tmp['publishers'] = [
        {
            'name': ['Editions de la Centrale'],
            'place': ['Martigny']
        }
    ]

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['publishers'][0]['name'][0] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['publishers'][0]['place'][0] = [2]
        validate(document_data_tmp, document_schema)


def test_publicationYear(document_schema, document_data_tmp):
    """Test publicationYear for jsonschemas."""
    document_data_tmp['publicationYear'] = 2017

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['publicationYear'] = ['2017']
        validate(document_data_tmp, document_schema)


def test_freeFormedPublicationDate(document_schema, document_data_tmp):
    """Test freeFormedPublicationDate for jsonschemas."""
    document_data_tmp['freeFormedPublicationDate'] = '2017'

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['freeFormedPublicationDate'] = [2]
        validate(document_data_tmp, document_schema)


def test_extent(document_schema, document_data_tmp):
    """Test extent for jsonschemas."""
    document_data_tmp['extent'] = '117'

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['extent'] = [2]
        validate(document_data_tmp, document_schema)


def test_otherMaterialCharacteristics(
        document_schema, document_data_tmp):
    """Test otherMaterialCharacteristics for jsonschemas."""
    document_data_tmp['otherMaterialCharacteristics'] = 'ill.'

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['otherMaterialCharacteristics'] = [2]
        validate(document_data_tmp, document_schema)


def test_formats(document_schema, document_data_tmp):
    """Test formats for jsonschemas."""
    document_data_tmp['formats'] = ['15 x 22 cm']

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['formats'] = 'string is a bad type'
        validate(document_data_tmp, document_schema)


def test_additionalMaterials(document_schema, document_data_tmp):
    """Test additionalMaterials for jsonschemas."""
    document_data_tmp['additionalMaterials'] = '1 CD-ROM'

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['additionalMaterials'] = 2
        validate(document_data_tmp, document_schema)


def test_series(document_schema, document_data_tmp):
    """Test series for jsonschemas."""
    document_data_tmp['series'] = [
        {
            'name': 'Les débuts de la suite',
            'number': '1'
        },
        {
            'name': 'Autre collection',
            'number': '2'
        }
    ]

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['series'][0]['name'] = 2
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['series'][0]['number'] = 2
        validate(document_data_tmp, document_schema)


def test_notes(document_schema, document_data_tmp):
    """Test notes for jsonschemas."""
    document_data_tmp['notes'] = ["Photo de l'auteur sur le 4e de couv."]

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['notes'][0] = 2
        validate(document_data_tmp, document_schema)


def test_abstracts(document_schema, document_data_tmp):
    """Test abstracts for jsonschemas."""
    document_data_tmp['abstracts'] = ["This document is about..."]

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['abstracts'][0] = 2
        validate(document_data_tmp, document_schema)


def test_identifiedby(document_schema, document_data_tmp):
    """Test identifiers for jsonschemas."""
    document_data_tmp['identifiedBy'] = [
        {
            "type": "bf:Local",
            "source": "RERO",
            "value": "R008745599"
        },
        {
            "type": "bf:Isbn",
            "value": "9782844267788"
        },
        {
            "type": "bf:Local",
            "source": "BNF",
            "value": "FRBNF452959040000002"
        },
        {
            "type": "uri",
            "value": "http://catalogue.bnf.fr/ark:/12148/cb45295904f"
        }
    ]
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        for identifier in document_data_tmp['identifiedBy']:
            identifier['value'] = 2
            validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['identifiedBy'] = {}
        validate(document_data_tmp, document_schema)


def test_subjects(document_schema, document_data_tmp):
    """Test subjects for jsonschemas."""
    document_data_tmp['subjects'] = [
        'ILS',
        'informatique',
        'bibliothèque'
    ]

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['subjects'] = 2
        validate(document_data_tmp, document_schema)


def test_harvested(document_schema, document_data_tmp):
    """Test harvested for jsonschemas."""
    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['harvested'] = 2
        validate(document_data_tmp, document_schema)
