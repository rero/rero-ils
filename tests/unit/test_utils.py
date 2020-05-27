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

from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import add_years, extracted_data_from_ref, \
    get_endpoint_configuration, get_schema_for_resource, read_json_record
from rero_ils.utils import get_current_language, unique_list


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
    json_schema = 'https://ils.rero.ch/schema/patrons/patron-v0.0.1.json'
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
    ptty = patron_sion_data['patron_type']
    print(ptty)
    assert extracted_data_from_ref(ptty, data='pid') == 'ptty4'
    assert extracted_data_from_ref(ptty, data='resource') == 'patron_types'
    assert extracted_data_from_ref(ptty, data='record_class') == PatronType
    ptty_record = extracted_data_from_ref(ptty, data='record')
    assert ptty_record.pid == patron_type_grown_sion.pid

    # check dummy data
    assert extracted_data_from_ref('dummy_data', data='pid') is None
    assert extracted_data_from_ref('dummy_data', data='resource') is None
    assert extracted_data_from_ref('dummy_data', data='record_class') is None
    assert extracted_data_from_ref('dummy_data', data='record') is None
    assert extracted_data_from_ref(ptty, data='dummy') is None


def test_current_language(app):
    """Test current language."""
    # Just test this function return otherwise than None
    assert get_current_language()
