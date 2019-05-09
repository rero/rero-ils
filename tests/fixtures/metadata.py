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

"""Common pytest fixtures and plugins."""

import json
from copy import deepcopy
from os.path import dirname, join

import mock
import pytest
from invenio_circulation.proxies import current_circulation
from utils import flush_index, mock_response

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy
from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.item_types.api import ItemType, ItemTypesSearch
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.mef_persons.api import MefPerson, MefPersonsSearch
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch
from rero_ils.modules.patrons.api import Patron, PatronsSearch


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
