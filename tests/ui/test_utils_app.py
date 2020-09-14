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

from rero_ils.modules.documents.api import Document
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import get_record_class_from_schema_or_pid_type, \
    get_ref_for_pid, pids_exists_in_data
from rero_ils.utils import get_current_language, remove_empties_from_dict


def test_get_ref_for_pid(app):
    """Test get $ref for pid."""
    url = 'https://ils.rero.ch/api/documents/3'
    assert get_ref_for_pid('documents', '3') == url
    assert get_ref_for_pid('doc', '3') == url
    assert get_ref_for_pid(Document, '3') == url
    assert get_ref_for_pid('test', '3') is None


def test_remove_empties_form_dict():
    """Test remove empties data from dict."""
    data = {
        'key1': '',
        'key2': [],
        'key3': {
            'key31': None
        }
    }
    cleaned_data = remove_empties_from_dict(data)
    assert not cleaned_data


def test_pids_exists_in_data(app, org_martigny, lib_martigny):
    """Test pid exists."""
    ok = pids_exists_in_data(
        info='test',
        data={
            'organisation': {
                '$ref': 'https://ils.rero.ch/api/organisations/org1'
            }
        },
        required={'org': 'organisation'},
        not_required={'lib': 'library'}
    )
    assert ok == []

    ok = pids_exists_in_data(
        info='test',
        data={},
        required={'org': 'organisation'},
        not_required={'lib': 'library'}
    )
    assert ok == ['test: No data found: organisation']

    ok = pids_exists_in_data(
        info='test',
        data={
            'organisation': {
                '$ref': 'https://ils.rero.ch/api/xxxx/org2'
            },
        },
        required={'org': 'organisation'},
        not_required={'lib': 'library'}
    )
    assert ok == [
        "test: No pid found: org {'$ref': 'https://ils.rero.ch/api/xxxx/org2'}"
    ]

    ok = pids_exists_in_data(
        info='test',
        data={
            'organisation': {
                '$ref': 'https://ils.rero.ch/api/organisations/org2'
            },
            'library': {
                '$ref': 'https://ils.rero.ch/api/libraries/lib1'
            }
        },
        required={'org': 'organisation'},
        not_required={'lib': 'library'}
    )
    assert ok == ['test: Pid does not exist: org org2']


def test_get_language(app):
    """Test get the current language of the application."""
    assert get_current_language() == 'en'


def test_get_record_class_from_schema_or_pid_type(app):
    """Test get record class from schema or pid_type."""
    schema = 'https://ils.rero.ch/schemas/documents/document-v0.0.1.json'
    assert get_record_class_from_schema_or_pid_type(schema=schema) == Document
    assert get_record_class_from_schema_or_pid_type(pid_type='doc') == Document
    assert get_record_class_from_schema_or_pid_type(
        schema=schema, pid_type='doc') == Document
    assert get_record_class_from_schema_or_pid_type(
        schema=schema, pid_type='ptrn') == Document

    schema = 'https://ils.rero.ch/schemas/patrons/patron-v0.0.1.json'
    assert get_record_class_from_schema_or_pid_type(
        schema=schema, pid_type='doc') == Patron
    assert get_record_class_from_schema_or_pid_type(
        schema=schema, pid_type='ptrn') == Patron
    assert get_record_class_from_schema_or_pid_type(pid_type='ptrn') == Patron

    assert not get_record_class_from_schema_or_pid_type(pid_type='toto')
    assert not get_record_class_from_schema_or_pid_type(
        schema='toto', pid_type=None)
    assert not get_record_class_from_schema_or_pid_type(
        schema='toto', pid_type='toto')
    assert not get_record_class_from_schema_or_pid_type(
        schema=None, pid_type=None)
    assert not get_record_class_from_schema_or_pid_type(
        schema=None, pid_type='toto')
    assert not get_record_class_from_schema_or_pid_type(schema=None)
    assert not get_record_class_from_schema_or_pid_type(pid_type=None)
    assert not get_record_class_from_schema_or_pid_type()
