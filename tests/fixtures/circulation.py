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
def roles(base_app, database):
    """Create user roles."""
    ds = base_app.extensions['invenio-accounts'].datastore
    ds.create_role(name='patron')
    ds.create_role(name='librarian')
    ds.create_role(name='system_librarian')
    ds.commit()


@pytest.fixture(scope="module")
def patron_martigny_data(data):
    """Load Martigny patron data."""
    return deepcopy(data.get('ptrn5'))


@pytest.fixture(scope="function")
def patron_martigny_data_tmp(data):
    """Load Martigny patron data scope function."""
    return deepcopy(data.get('ptrn5'))


@pytest.fixture(scope="module")
def patron_martigny(
        app,
        roles,
        lib_martigny,
        patron_type_children_martigny,
        patron_martigny_data):
    """Create Martigny patron record."""
    ptrn = Patron.create(
        data=patron_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def patron_martigny_no_email(
        app,
        roles,
        patron_type_children_martigny,
        patron_martigny_data):
    """Create Martigny patron without sending reset password instruction."""
    ptrn = Patron.create(
        data=patron_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian_martigny_no_email(
        app,
        roles,
        lib_martigny,
        patron_type_children_martigny,
        librarian_martigny_data):
    """Create Martigny librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def librarian_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(data.get('ptrn1'))


@pytest.fixture(scope="function")
def librarian_martigny_data_tmp(data):
    """Load Martigny librarian data scope function."""
    return deepcopy(data.get('ptrn1'))


@pytest.fixture(scope="module")
def librarian_martigny(
        app,
        roles,
        lib_martigny,
        patron_type_children_martigny,
        librarian_martigny_data):
    """Create Martigny librarian record."""
    ptrn = Patron.create(
        data=librarian_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def librarian_saxon_data(data):
    """Load Saxon librarian data."""
    return deepcopy(data.get('ptrn2'))


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian_saxon_no_email(
        app,
        roles,
        lib_saxon,
        patron_type_children_martigny,
        librarian_saxon_data):
    """Create Martigny patron record no email."""
    ptrn = Patron.create(
        data=librarian_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def librarian_saxon(
        app,
        roles,
        lib_saxon,
        patron_type_adults_martigny,
        librarian_saxon_data):
    """Create Saxon librarian record."""
    ptrn = Patron.create(
        data=librarian_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def librarian_fully_data(data):
    """Load fully librarian data."""
    return deepcopy(data.get('ptrn3'))


@pytest.fixture(scope="module")
def librarian_fully(
        app,
        roles,
        lib_fully,
        patron_type_adults_martigny,
        librarian_fully_data):
    """Create Fully librarian record."""
    ptrn = Patron.create(
        data=librarian_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def librarian_sion_data(data):
    """Load sion librarian data."""
    return deepcopy(data.get('ptrn4'))


@pytest.fixture(scope="module")
def librarian_sion(
        app,
        roles,
        lib_sion,
        patron_type_youngsters_sion,
        librarian_sion_data):
    """Create sion librarian record."""
    ptrn = Patron.create(
        data=librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian_sion_no_email(
        app,
        roles,
        lib_sion,
        patron_type_youngsters_sion,
        librarian_sion_data):
    """Create sion librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def loan_data(data):
    """Load loan data."""
    return deepcopy(data.get('loan1'))


@pytest.fixture(scope="function")
def loan_data_tmp(data):
    """Load loan data scope function."""
    return deepcopy(data.get('loan1'))


@pytest.fixture(scope="module")
def loan_pending(
        app,
        item_lib_fully,
        loc_public_martigny,
        lib_martigny,
        loan_data):
    """Create loan record with state pending.

    item_lib_fully is requested by librarian_martigny(patron).
    """
    loan = Loan.create(
        data=loan_data,
        delete_pid=True,
        dbcommit=True,
        reindex=True)
    flush_index(current_circulation.loan_search.Meta.index)
    return loan
