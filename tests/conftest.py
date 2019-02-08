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
from utils import flush_index

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
def data():
    """."""
    with open(join(dirname(__file__), 'data/data.json')) as f:
        data = json.load(f)
        return data


@pytest.fixture(scope="module")
def organisation_data(data):
    """."""
    return (data.get('org1'))


@pytest.fixture(scope="module")
def library_data(data):
    """."""
    return deepcopy(data.get('lib1'))


@pytest.fixture(scope="module")
def location_data(data):
    """."""
    return deepcopy(data.get('loc1'))


@pytest.fixture(scope="module")
def store_location_data(data):
    """."""
    return deepcopy(data.get('loc2'))


@pytest.fixture(scope="module")
def circ_policy_data(data):
    """."""
    return deepcopy(data.get('cipo1'))


@pytest.fixture(scope="function")
def circ_policy_data_tmp(data):
    """."""
    return deepcopy(data.get('cipo1'))


@pytest.fixture(scope="module")
def item_type_data(data):
    """."""
    return deepcopy(data.get('itty1'))


@pytest.fixture(scope="function")
def item_type_data_tmp(data):
    """."""
    return deepcopy(data.get('itty1'))


@pytest.fixture(scope="module")
def patron_type_data(data):
    """."""
    return deepcopy(data.get('ptty1'))


@pytest.fixture(scope="function")
def patron_type_data_tmp(data):
    """."""
    return deepcopy(data.get('ptty1'))


@pytest.fixture(scope="module")
def document_data(data):
    """."""
    return deepcopy(data.get('doc1'))


@pytest.fixture(scope="function")
def document_data_tmp(data):
    """."""
    return deepcopy(data.get('doc1'))


@pytest.fixture(scope="module")
def user_librarian_data(data):
    """."""
    return deepcopy(data.get('ptrn1'))


@pytest.fixture(scope="module")
def user_patron_data(data):
    """."""
    return deepcopy(data.get('ptrn2'))


@pytest.fixture(scope="function")
def user_librarian_data_tmp(data):
    """."""
    return deepcopy(data.get('ptrn1'))


@pytest.fixture(scope="module")
def mef_person_data(data):
    """."""
    return deepcopy(data.get('pers1'))


@pytest.fixture(scope="function")
def mef_person_data_tmp(data):
    """."""
    return deepcopy(data.get('pers1'))


@pytest.fixture(scope="module")
def loan_data(data):
    """."""
    return deepcopy(data.get('loan1'))


@pytest.fixture(scope="function")
def loan_data_tmp(data):
    """."""
    return deepcopy(data.get('loan1'))


@pytest.fixture(scope="module")
def item_on_loan_data(data):
    """."""
    return deepcopy(data.get('item1'))


@pytest.fixture(scope="module")
def item_on_shelf_data(data):
    """."""
    return deepcopy(data.get('item2'))


@pytest.fixture(scope="function")
def item_on_loan_data_tmp(data):
    """."""
    return deepcopy(data.get('item1'))


@pytest.fixture(scope="module")
def organisation(database, organisation_data):
    """."""
    org = Organisation.create(
        data=organisation_data,
        delete_pid=False,
        dbcommit=True)
    return org


@pytest.fixture(scope="module")
def library(app, organisation, library_data):
    """."""
    lib = Library.create(
        data=library_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LibrariesSearch.Meta.index)
    return lib


@pytest.fixture(scope="module")
def location(app, library, location_data):
    """."""
    loc = Location.create(
        data=location_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def store_location(location, store_location_data):
    """."""
    loc = Location.create(
        data=store_location_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def circ_policy(app, organisation, circ_policy_data):
    """."""
    cipo = CircPolicy.create(
        data=circ_policy_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    return cipo


@pytest.fixture(scope="module")
def item_type(app, organisation, item_type_data):
    """."""
    itty = ItemType.create(
        data=item_type_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def patron_type(app, organisation, patron_type_data):
    """."""
    ptty = PatronType.create(
        data=patron_type_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronTypesSearch.Meta.index)
    return ptty


@pytest.fixture(scope="module")
def roles(base_app, database):
    """."""
    ds = base_app.extensions['invenio-accounts'].datastore
    ds.create_role(name='patron')
    ds.create_role(name='librarian')
    ds.commit()


@pytest.fixture(scope="module")
def user_librarian(app, roles, library, patron_type,
                   user_librarian_data):
    """."""
    ptrn = Patron.create(
        data=user_librarian_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def user_patron(app, roles, library, user_librarian_type,
                user_patron_data):
    """."""
    ptrn = Patron.create(
        data=user_patron_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def mef_person(app, mef_person_data):
    """."""
    pers = MefPerson.create(
        data=mef_person_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(MefPersonsSearch.Meta.index)
    return pers


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def user_librarian_no_email(app, roles, library, patron_type,
                            user_librarian_data):
    """."""
    ptrn = Patron.create(
        data=user_librarian_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def user_patron_no_email(app, roles, library, patron_type, user_patron_data):
    """."""
    ptrn = Patron.create(
        data=user_patron_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def document(app, document_data):
    """."""
    doc = Document.create(
        data=document_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    return doc


@pytest.fixture(scope="module")
def loan(app, item_on_loan, location, library, loan_data):
    """."""
    loan = Loan.create(
        data=loan_data,
        delete_pid=True,
        dbcommit=True,
        reindex=True)
    flush_index(current_circulation.loan_search.Meta.index)
    return loan


@pytest.fixture(scope="module")
def item_on_loan(app, document, item_on_loan_data, location, item_type):
    """."""
    item = Item.create(
        data=item_on_loan_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="module")
def item_on_shelf(app, document, item_on_shelf_data, location, item_type):
    """."""
    item = Item.create(
        data=item_on_shelf_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemsSearch.Meta.index)
    return item


@pytest.fixture(scope="session")
def json_header():
    """."""
    return [
        ('Accept', 'application/json'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope="session")
def can_delete_json_header():
    """."""
    return [
        ('Accept', 'application/can-delete+json'),
        ('Content-Type', 'application/json')
    ]


@pytest.fixture(scope='module')
def app_config(app_config):
    """Create temporary instance dir for each test."""
    app_config['RATELIMIT_STORAGE_URL'] = 'memory://'
    app_config['CACHE_TYPE'] = 'simple'
    app_config['SEARCH_ELASTIC_HOSTS'] = None
    app_config['DB_VERSIONING'] = True
    return app_config
