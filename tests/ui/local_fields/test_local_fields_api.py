# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Local fields Record tests."""

from __future__ import absolute_import, print_function

from utils import flush_index, get_mapping

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.local_fields.api import LocalField, LocalFieldsSearch
from rero_ils.modules.local_fields.api import local_field_id_fetcher as fetcher
from rero_ils.modules.utils import extracted_data_from_ref


def test_local_fields_es(client, local_field_martigny):
    """Test."""
    local_field = LocalField.get_local_fields_by_resource('doc', 'doc1')
    assert len(local_field) == 1

    local_field = LocalField.get_local_fields_by_resource(
        'doc', 'doc1', 'org2')
    assert len(local_field) == 0


def test_local_fields_es_mapping(db, org_sion, document,
                                 local_field_sion_data):
    """Test local fields elasticsearch mapping."""
    search = LocalFieldsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    lofi = LocalField.create(local_field_sion_data, dbcommit=True,
                             reindex=True, delete_pid=True)
    flush_index(LocalFieldsSearch.Meta.index)
    assert mapping == get_mapping(search.Meta.index)

    assert lofi == local_field_sion_data
    assert lofi.get('pid') == '1'

    lofi = LocalField.get_record_by_pid('1')
    assert lofi == local_field_sion_data

    fetched_pid = fetcher(lofi.id, lofi)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'lofi'

    document_pid = extracted_data_from_ref(lofi.get('parent'))
    search = DocumentsSearch().filter(
            'term', pid=document_pid)
    document = list(search.scan())[0].to_dict()
    for field in document['local_fields']:
        if field['organisation_pid'] == document_pid:
            assert field['fields'] ==\
                local_field_sion_data['fields']['field_1']
