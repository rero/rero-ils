# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""organisation JSON schema tests."""

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
        document_data_tmp['languages'][0]['language'] = [2]
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['languages'][0]['language'] = ['gre']
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


def test_identifiers(document_schema, document_data_tmp):
    """Test identifiers for jsonschemas."""
    document_data_tmp['identifiers'] = {
        "reroID": "R004567655",
        "isbn": "9782082015769",
        "bnfID": "cb350330441"
    }

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['identifiers']['reroID'] = 2
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['identifiers']['isbn'] = 2
        validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['identifiers'] = {}
        validate(document_data_tmp, document_schema)

    document_data_tmp['identifiers'] = {
        "bnfID": "cb350330441"
    }

    validate(document_data_tmp, document_schema)

    with pytest.raises(ValidationError):
        document_data_tmp['identifiers']['bnfID'] = 2
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
