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

"""Common pytest fixtures and plugins."""


from copy import deepcopy

import mock
import pytest
from utils import flush_index, mock_response

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.mef_persons.api import MefPerson, MefPersonsSearch


@pytest.fixture(scope="module")
def ebook_1_data(data):
    """Load ebook 1 data."""
    return deepcopy(data.get('ebook1'))


@pytest.fixture(scope="module")
def ebook_1(app, ebook_1_data):
    """Load ebook 1 record."""
    doc = Document.create(
        data=ebook_1_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def ebook_2_data(data):
    """Load ebook 2 data."""
    return deepcopy(data.get('ebook2'))


@pytest.fixture(scope="module")
def ebook_2(app, ebook_2_data):
    """Load ebook 2 record."""
    doc = Document.create(
        data=ebook_2_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def ebook_3_data(data):
    """Load ebook 3 data."""
    return deepcopy(data.get('ebook3'))


@pytest.fixture(scope="module")
def ebook_3(app, ebook_3_data):
    """Load ebook 3 record."""
    doc = Document.create(
        data=ebook_3_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def ebook_4_data(data):
    """Load ebook 4 data."""
    return deepcopy(data.get('ebook4'))


@pytest.fixture(scope="module")
def ebook_4(app, ebook_4_data):
    """Load ebook 4 record."""
    doc = Document.create(
        data=ebook_4_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_data(data):
    """Load document data."""
    return deepcopy(data.get('doc1'))


@pytest.fixture(scope="function")
def document_data_tmp(data):
    """Load document data scope function."""
    return deepcopy(data.get('doc1'))


@pytest.fixture(scope="module")
def document(app, document_data):
    """Load document record."""
    doc = Document.create(
        data=document_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_data_ref(data):
    """Load document ref data."""
    return deepcopy(data.get('doc2'))


@pytest.fixture(scope="module")
def mef_person_data(data):
    """Load mef person data."""
    return deepcopy(data.get('pers1'))


@pytest.fixture(scope="function")
def mef_person_data_tmp(data):
    """Load mef person data scope function."""
    return deepcopy(data.get('pers1'))


@pytest.fixture(scope="module")
def mef_person_response_data(mef_person_data):
    """Load mef person response data."""
    json_data = {
        'id': mef_person_data['pid'],
        'metadata': mef_person_data
    }
    return json_data


@pytest.fixture(scope="module")
def mef_person(app, mef_person_data):
    """Create mef person record."""
    pers = MefPerson.create(
        data=mef_person_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(MefPersonsSearch.Meta.index)
    return pers


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.documents.listener.requests_get')
@mock.patch('rero_ils.modules.documents.jsonresolver_mef_person.requests_get')
def document_ref(mock_resolver_get, mock_listener_get,
                 app, document_data_ref, mef_person_response_data):
    """Load document with mef records reference."""
    mock_resolver_get.return_value = mock_response(
        json_data=mef_person_response_data
    )
    mock_listener_get.return_value = mock_response(
        json_data=mef_person_response_data
    )
    doc = Document.create(
        data=document_data_ref,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def document_sion_items_data(data):
    """Load document data for sion items."""
    return deepcopy(data.get('doc3'))


@pytest.fixture(scope="function")
def document_sion_items_data_tmp(data):
    """Load document data for sion items scope function."""
    return deepcopy(data.get('doc3'))


@pytest.fixture(scope="module")
def document_sion_items(app, document_sion_items_data):
    """Create document data for sion items."""
    doc = Document.create(
        data=document_sion_items_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def item_lib_martigny_data(data):
    """Load item of martigny library."""
    return deepcopy(data.get('item1'))


@pytest.fixture(scope="function")
def item_lib_martigny_data_tmp(data):
    """Load item of martigny library scope function."""
    return deepcopy(data.get('item1'))


@pytest.fixture(scope="module")
def item_lib_martigny(
        app,
        document,
        item_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item of martigny library."""
    item = Item.create(
        data=item_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item2_lib_martigny_data(data):
    """Load item of martigny library."""
    return deepcopy(data.get('item5'))


@pytest.fixture(scope="function")
def item2_lib_martigny_data_tmp(data):
    """Load item of martigny library scope function."""
    return deepcopy(data.get('item5'))


@pytest.fixture(scope="module")
def item2_lib_martigny(
        app,
        document,
        item2_lib_martigny_data,
        loc_public_martigny,
        item_type_standard_martigny):
    """Create item2 of martigny library."""
    item = Item.create(
        data=item2_lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_saxon_data(data):
    """Load item of saxon library."""
    return deepcopy(data.get('item2'))


@pytest.fixture(scope="module")
def item_lib_saxon(
        app,
        document,
        item_lib_saxon_data,
        loc_public_saxon,
        item_type_standard_martigny):
    """Create item of saxon library."""
    item = Item.create(
        data=item_lib_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_fully_data(data):
    """Load item of fully library."""
    return deepcopy(data.get('item3'))


@pytest.fixture(scope="module")
def item_lib_fully(
        app,
        document,
        item_lib_fully_data,
        loc_public_fully,
        item_type_standard_martigny):
    """Create item of fully library."""
    item = Item.create(
        data=item_lib_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_sion_data(data):
    """Load item of sion library."""
    return deepcopy(data.get('item4'))


@pytest.fixture(scope="module")
def item_lib_sion(
        app,
        document_sion_items,
        item_lib_sion_data,
        loc_public_sion,
        item_type_regular_sion):
    """Create item of sion library."""
    item = Item.create(
        data=item_lib_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_lib_sion_org2_data(data):
    """Load item of sion library."""
    return deepcopy(data.get('item6'))


@pytest.fixture(scope="module")
def item_lib_sion_org2(
        app,
        document,
        item_lib_sion_org2_data,
        loc_restricted_sion,
        item_type_regular_sion):
    """Create item of sion library."""
    item = Item.create(
        data=item_lib_sion_org2_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item
