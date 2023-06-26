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

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError
from utils import flush_index

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.items.api import Item
from rero_ils.modules.local_fields.api import LocalField, LocalFieldsSearch
from rero_ils.modules.utils import get_ref_for_pid


def test_local_fields(
    client, org_martigny, document_data, local_field_martigny_data,
    item_lib_martigny, item_lib_martigny_data
):
    """Test local fields."""
    lofi_data = deepcopy(local_field_martigny_data)
    lofi_data.pop('pid', None)
    document_data.pop('pid', None)
    item_lib_martigny_data.pop('pid', None)

    # INIT :: Create a new Document and a new LocalField
    document = Document.create(document_data, dbcommit=True, reindex=True)
    lofi_data['parent']['$ref'] = \
        get_ref_for_pid(document.provider.pid_type, document.pid)
    local_field = LocalField.create(lofi_data, dbcommit=True, reindex=True)

    # TEST#1 :: get LocalFields
    fields = LocalField.get_local_fields_by_id('doc', document.pid)
    assert len(list(fields)) == 1
    fields = LocalField.get_local_fields(document, 'org2')
    assert not list(fields)

    # TEST#2 :: Delete the LocalField
    #    Ensure the document index reflects changes
    local_field.delete(delindex=True)
    flush_index(LocalFieldsSearch.Meta.index)
    flush_index(DocumentsSearch.Meta.index)

    es_doc = DocumentsSearch().get_record_by_pid(document.pid).to_dict()
    assert 'local_fields' not in es_doc

    # TEST#3 :: Delete the document
    #   - Add new LocalFields on the document
    #   - Ensure this LocalField is related to the document, but it's not a
    #     cause to block the document suppression
    #   - Delete the document and ensure the LocalField is now deleted.
    #   - Ensure the LocalField index is coherent
    assert 'local_fields' not in document.get_links_to_me()
    lofi_data.pop('pid', None)
    local_field = LocalField.create(lofi_data, dbcommit=True, reindex=True)
    assert document.get_links_to_me()['local_fields'] == 1
    assert 'local_fields' not in \
           document.reasons_not_to_delete().get('links', {})
    parent_pid = document.pid
    document.delete(delindex=True)
    assert not LocalField.get_record_by_pid(local_field.pid)
    fields = LocalField.get_local_fields_by_id('doc', parent_pid)
    assert len(list(fields)) == 0

    # TEST#4 :: Same as previous but for item.
    del item_lib_martigny_data['barcode']
    item = Item.create(item_lib_martigny_data, dbcommit=True, reindex=True)
    assert 'local_fields' not in item.get_links_to_me()
    lofi_data.pop('pid', None)
    lofi_data['parent']['$ref'] = \
        get_ref_for_pid(item.provider.pid_type, item.pid)
    local_field = LocalField.create(lofi_data, dbcommit=True, reindex=True)
    assert item.get_links_to_me()['local_fields'] == 1
    assert 'local_fields' not in \
           item.reasons_not_to_delete().get('links', {})
    parent_pid = item.pid
    item.delete(delindex=True)
    assert not LocalField.get_record_by_pid(local_field.pid)
    fields = LocalField.get_local_fields_by_id('item', parent_pid)
    assert len(list(fields)) == 0


def test_local_fields_extended_validation(
    document, document2_ref, local_field_martigny, local_field_martigny_data
):
    """Test local fields extended validation."""
    lofi_data = deepcopy(local_field_martigny_data)
    lofi_data.pop('pid', None)

    # TEST#1 :: unknown parent resource
    lofi_data['parent']['$ref'] = get_ref_for_pid('doc', 'dummy')
    with pytest.raises(ValidationError) as err:
        LocalField.create(lofi_data)
    assert "Parent record doesn't exists." in str(err)

    # TEST#2 :: empty fields
    lofi_data = deepcopy(local_field_martigny_data)
    lofi_data.pop('pid', None)
    lofi_data['parent']['$ref'] = get_ref_for_pid('doc', document2_ref.pid)
    lofi_data['fields'] = {}
    with pytest.raises(ValidationError) as err:
        LocalField.create(lofi_data)
    assert 'Missing fields.' in str(err)

    # TEST#3 :: resource unicity for local fields
    lofi_data = deepcopy(local_field_martigny_data)
    lofi_data.pop('pid', None)
    with pytest.raises(ValidationError) as err:
        LocalField.create(lofi_data)
    assert 'Local fields already exist for this resource.' in str(err)
