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

"""Test utils."""

import os
from datetime import datetime

import pytest

from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import PasswordValidatorException, add_years, \
    extracted_data_from_ref, get_endpoint_configuration, \
    get_schema_for_resource, password_generator, password_validator, \
    read_json_record
from rero_ils.utils import get_current_language, language_iso639_2to1, \
    language_mapping, unique_list


def test_unique_list():
    """Test unicity of list."""
    list = ['python', 'snail', 'python', 'snail']
    assert ['python', 'snail'] == unique_list(list)


def test_read_json_record(request):
    """Test IlsRecord PID after validation failed"""
    file_name = os.path.join(request.fspath.dirname, '..', 'data',
                             'documents.json')
    with open(file_name) as json_file:
        count = 0
        for record in read_json_record(json_file):
            count += 1
            assert record.get('pid') == str(count)
        assert count == 2


def test_add_years():
    """Test adding years to a date."""
    initial_date = datetime.now()
    one_year_later = add_years(initial_date, 1)
    assert initial_date.year == one_year_later.year - 1

    initial_date = datetime.strptime('2020-02-29', '%Y-%m-%d')
    tow_years_later = add_years(initial_date, 2)
    four_years_later = add_years(initial_date, 4)
    assert tow_years_later.month == 3 and tow_years_later.day == 1
    assert four_years_later.month == initial_date.month and \
        four_years_later.day == initial_date.day


def test_get_schema_for_resources(app):
    """Test get_schemas_for_resource function."""
    json_schema = 'https://bib.rero.ch/schemas/patrons/patron-v0.0.1.json'
    assert get_schema_for_resource(Patron) == json_schema
    assert get_schema_for_resource('ptrn') == json_schema


def test_get_endpoint_configuration(app):
    """Test get_endpoint_configuration."""
    assert get_endpoint_configuration('loc')['pid_type'] == 'loc'
    assert get_endpoint_configuration('locations')['pid_type'] == 'loc'
    assert get_endpoint_configuration(PatronType)['pid_type'] == 'ptty'
    assert get_endpoint_configuration('dummy') is None


def test_extract_data_from_ref(app, patron_sion_data,
                               patron_type_grown_sion):
    """Test extract_data_from_ref."""
    # Check real data
    ptty = patron_sion_data['patron']['type']
    assert extracted_data_from_ref(ptty, data='pid') == 'ptty4'
    assert extracted_data_from_ref(ptty, data='resource') == 'patron_types'
    assert extracted_data_from_ref(ptty, data='record_class') == PatronType
    ptty_record = extracted_data_from_ref(ptty, data='record')
    assert ptty_record.pid == patron_type_grown_sion.pid
    assert extracted_data_from_ref(ptty, data='es_record')['pid'] == 'ptty4'

    # check dummy data
    assert extracted_data_from_ref('dummy_data', data='pid') is None
    assert extracted_data_from_ref('dummy_data', data='resource') is None
    assert extracted_data_from_ref('dummy_data', data='record_class') is None
    assert extracted_data_from_ref('dummy_data', data='record') is None
    assert extracted_data_from_ref(ptty, data='dummy') is None
    assert extracted_data_from_ref('dummy_data', data='es_record') is None


def test_current_language(app):
    """Test current language."""
    # Just test this function return otherwise than None
    assert get_current_language()


def test_language_iso639_2to1(app):
    """Test convert MARC language code to language."""
    assert language_iso639_2to1('eng') == 'en'
    assert language_iso639_2to1('fre') == 'fr'
    assert language_iso639_2to1('ger') == 'de'
    assert language_iso639_2to1('ita') == 'it'
    # default language
    assert language_iso639_2to1('rus') == 'en'


def test_language_mapping(app):
    """Test language mapping."""
    assert 'fre' == language_mapping('fre')
    assert 'dut' == language_mapping('dum')


def test_password_validator():
    """Test password validator."""
    with pytest.raises(PasswordValidatorException):
        password_validator('foo')
        password_validator('foobarbar')
        password_validator('1244567899')
        password_validator('foobar123')
        password_validator('FooBar123', length=12)

    assert password_validator('FooBar12')
    assert password_validator('FooBar123')
    assert password_validator('Foo Bar 123')
    assert password_validator('FooBar123$', special_char=True)


def test_password_generator():
    """Test password generator."""
    assert len(password_generator()) == 8
    assert len(password_generator(length=12)) == 12
    assert password_validator(password_generator())
    with pytest.raises(Exception):
        password_generator(length=2)
        password_generator(length=3, special_char=True)
