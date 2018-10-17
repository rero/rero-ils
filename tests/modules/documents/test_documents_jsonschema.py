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


def test_required(document_schema, minimal_document_record):
    """Test required for jsonschemas."""
    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        validate({}, document_schema)


def test_pid(document_schema, minimal_document_record):
    """Test pid for jsonschemas."""
    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['pid'] = 25
        validate(minimal_document_record, document_schema)


def test_title(document_schema, minimal_document_record):
    """Test title for jsonschemas."""
    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['title'] = 2
        validate(minimal_document_record, document_schema)


def test_titlesProper(document_schema, minimal_document_record):
    """Test titlesProper for jsonschemas."""
    minimal_document_record['titlesProper'] = ['RERO21 pour les nuls']

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['titlesProper'] = 'string is a bad type'
        validate(minimal_document_record, document_schema)


def test_type(document_schema, minimal_document_record):
    """Test type for document jsonschemas."""
    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['type'] = 2
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['type'] = 'CD-ROM'
        validate(minimal_document_record, document_schema)


def test_is_part_of(document_schema, minimal_document_record):
    """Test type for document jsonschemas."""
    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['is_part_of'] = 2
        validate(minimal_document_record, document_schema)


def test_languages(document_schema, minimal_document_record):
    """Test languages for jsonschemas."""
    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['languages'][0]['language'] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['languages'][0]['language'] = ['gre']
        validate(minimal_document_record, document_schema)


def test_translatedFrom(document_schema, minimal_document_record):
    """Test translatedFrom for jsonschemas."""
    minimal_document_record['translatedFrom'] = ['eng']

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['translatedFrom'] = [2]
        validate(minimal_document_record, document_schema)


def test_authors(document_schema, minimal_document_record):
    """Test authors for jsonschemas."""
    minimal_document_record['authors'] = [
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

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['authors'][0]['name'] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['authors'][0]['type'] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['authors'][0]['date'] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['authors'][0]['qualifier'] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['authors'][1]['type'] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['authors'][1]['name'] = [2]
        validate(minimal_document_record, document_schema)


def test_publishers(document_schema, minimal_document_record):
    """Test publishers for jsonschemas."""
    minimal_document_record['publishers'] = [
        {
            'name': ['Editions de la Centrale'],
            'place': ['Martigny']
        }
    ]

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['publishers'][0]['name'][0] = [2]
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['publishers'][0]['place'][0] = [2]
        validate(minimal_document_record, document_schema)


def test_publicationYear(document_schema, minimal_document_record):
    """Test publicationYear for jsonschemas."""
    minimal_document_record['publicationYear'] = 2017

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['publicationYear'] = ['2017']
        validate(minimal_document_record, document_schema)


def test_freeFormedPublicationDate(document_schema, minimal_document_record):
    """Test freeFormedPublicationDate for jsonschemas."""
    minimal_document_record['freeFormedPublicationDate'] = '2017'

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['freeFormedPublicationDate'] = [2]
        validate(minimal_document_record, document_schema)


def test_extent(document_schema, minimal_document_record):
    """Test extent for jsonschemas."""
    minimal_document_record['extent'] = '117'

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['extent'] = [2]
        validate(minimal_document_record, document_schema)


def test_otherMaterialCharacteristics(
        document_schema, minimal_document_record):
    """Test otherMaterialCharacteristics for jsonschemas."""
    minimal_document_record['otherMaterialCharacteristics'] = 'ill.'

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['otherMaterialCharacteristics'] = [2]
        validate(minimal_document_record, document_schema)


def test_formats(document_schema, minimal_document_record):
    """Test formats for jsonschemas."""
    minimal_document_record['formats'] = ['15 x 22 cm']

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['formats'] = 'string is a bad type'
        validate(minimal_document_record, document_schema)


def test_additionalMaterials(document_schema, minimal_document_record):
    """Test additionalMaterials for jsonschemas."""
    minimal_document_record['additionalMaterials'] = '1 CD-ROM'

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['additionalMaterials'] = 2
        validate(minimal_document_record, document_schema)


def test_series(document_schema, minimal_document_record):
    """Test series for jsonschemas."""
    minimal_document_record['series'] = [
        {
            'name': 'Les débuts de la suite',
            'number': '1'
        },
        {
            'name': 'Autre collection',
            'number': '2'
        }
    ]

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['series'][0]['name'] = 2
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['series'][0]['number'] = 2
        validate(minimal_document_record, document_schema)


def test_notes(document_schema, minimal_document_record):
    """Test notes for jsonschemas."""
    minimal_document_record['notes'] = ["Photo de l'auteur sur le 4e de couv."]

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['notes'][0] = 2
        validate(minimal_document_record, document_schema)


def test_abstracts(document_schema, minimal_document_record):
    """Test abstracts for jsonschemas."""
    minimal_document_record['abstracts'] = ["This document is about..."]

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['abstracts'][0] = 2
        validate(minimal_document_record, document_schema)


def test_identifiers(document_schema, minimal_document_record):
    """Test identifiers for jsonschemas."""
    minimal_document_record['identifiers'] = {
        "reroID": "R004567655",
        "isbn": "9782082015769",
        "bnfID": "cb350330441"
    }

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['identifiers']['reroID'] = 2
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['identifiers']['isbn'] = 2
        validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['identifiers'] = {}
        validate(minimal_document_record, document_schema)

    minimal_document_record['identifiers'] = {
        "bnfID": "cb350330441"
    }

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['identifiers']['bnfID'] = 2
        validate(minimal_document_record, document_schema)


def test_subjects(document_schema, minimal_document_record):
    """Test subjects for jsonschemas."""
    minimal_document_record['subjects'] = [
        'ILS',
        'informatique',
        'bibliothèque'
    ]

    validate(minimal_document_record, document_schema)

    with pytest.raises(ValidationError):
        minimal_document_record['subjects'] = 2
        validate(minimal_document_record, document_schema)
