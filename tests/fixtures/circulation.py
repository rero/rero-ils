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
from datetime import datetime, timezone

import mock
import pytest
from invenio_circulation.search.api import LoansSearch
from utils import flush_index

from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.notifications.api import NotificationsSearch, \
    get_availability_notification
from rero_ils.modules.patrons.api import Patron, PatronsSearch


@pytest.fixture(scope="module")
def roles(base_app, database):
    """Create user roles."""
    ds = base_app.extensions['invenio-accounts'].datastore
    ds.create_role(name='patron')
    ds.create_role(name='librarian')
    ds.create_role(name='system_librarian')
    ds.commit()


# ------------ Org: Martigny, Lib: Martigny, System Librarian ----------
@pytest.fixture(scope="module")
def system_librarian_martigny_data(data):
    """Load Martigny system librarian data."""
    return deepcopy(data.get('ptrn1'))


@pytest.fixture(scope="function")
def system_librarian_martigny_data_tmp(data):
    """Load Martigny system librarian data scope function."""
    return deepcopy(data.get('ptrn1'))


@pytest.fixture(scope="module")
def system_librarian_martigny(
        app,
        roles,
        lib_martigny,
        system_librarian_martigny_data):
    """Create Martigny system librarian record."""
    ptrn = Patron.create(
        data=system_librarian_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def system_librarian_martigny_no_email(
        app,
        roles,
        lib_martigny,
        system_librarian_martigny_data):
    """Create Martigny system librarian without sending reset password."""
    ptrn = Patron.create(
        data=system_librarian_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Martigny, Lib: Martigny, Librarian 1 ----------
@pytest.fixture(scope="module")
def librarian_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(data.get('ptrn2'))


@pytest.fixture(scope="function")
def librarian_martigny_data_tmp(data):
    """Load Martigny librarian data scope function."""
    return deepcopy(data.get('ptrn2'))


@pytest.fixture(scope="module")
def librarian_martigny(
        app,
        roles,
        lib_martigny,
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
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian_martigny_no_email(
        app,
        roles,
        lib_martigny,
        librarian_martigny_data):
    """Create Martigny librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Martigny, Lib: Martigny, Librarian 2 ----------
@pytest.fixture(scope="module")
def librarian2_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(data.get('ptrn3'))


@pytest.fixture(scope="function")
def librarian2_martigny_data_tmp(data):
    """Load Martigny librarian data scope function."""
    return deepcopy(data.get('ptrn3'))


@pytest.fixture(scope="module")
def librarian2_martigny(
        app,
        roles,
        lib_martigny,
        librarian2_martigny_data):
    """Create Martigny librarian record."""
    ptrn = Patron.create(
        data=librarian2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Martigny, Lib: Saxon, Librarian 1 ----------
@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian2_martigny_no_email(
        app,
        roles,
        lib_martigny,
        librarian2_martigny_data):
    """Create Martigny librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Martigny, Lib: Saxon, Librarian 1 ----------
@pytest.fixture(scope="module")
def librarian_saxon_data(data):
    """Load Saxon librarian data."""
    return deepcopy(data.get('ptrn4'))


@pytest.fixture(scope="function")
def librarian_saxon_data_tmp(data):
    """Load Saxon librarian data scope function."""
    return deepcopy(data.get('ptrn4'))


@pytest.fixture(scope="module")
def librarian_saxon(
        app,
        roles,
        lib_saxon,
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
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian_saxon_no_email(
        app,
        roles,
        lib_saxon,
        librarian_saxon_data):
    """Create Saxon librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Martigny, Lib: Fully, Librarian 1 ----------
@pytest.fixture(scope="module")
def librarian_fully_data(data):
    """Load Fully librarian data."""
    return deepcopy(data.get('ptrn5'))


@pytest.fixture(scope="function")
def librarian_fully_data_tmp(data):
    """Load Fully librarian data scope function."""
    return deepcopy(data.get('ptrn5'))


@pytest.fixture(scope="module")
def librarian_fully(
        app,
        roles,
        lib_fully,
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
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def librarian_fully_no_email(
        app,
        roles,
        lib_fully,
        librarian_fully_data):
    """Create Fully librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Martigny Patron 1 ----------
@pytest.fixture(scope="module")
def patron_martigny_data(data):
    """Load Martigny patron data."""
    return deepcopy(data.get('ptrn6'))


@pytest.fixture(scope="function")
def patron_martigny_data_tmp(data):
    """Load Martigny patron data scope function."""
    return deepcopy(data.get('ptrn6'))


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


# ------------ Org: Martigny Patron 1 ----------
@pytest.fixture(scope="module")
def patron_martigny_data(data):
    """Load Martigny patron data."""
    return deepcopy(data.get('ptrn6'))


@pytest.fixture(scope="function")
def patron_martigny_data_tmp(data):
    """Load Martigny patron data scope function."""
    return deepcopy(data.get('ptrn6'))


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


# ------------ Org: Martigny Patron 2 ----------
@pytest.fixture(scope="module")
def patron2_martigny_data(data):
    """Load Martigny patron data."""
    return deepcopy(data.get('ptrn7'))


@pytest.fixture(scope="module")
def patron2_martigny(
        app,
        roles,
        lib_martigny,
        patron_type_adults_martigny,
        patron2_martigny_data):
    """Create Martigny patron record."""
    ptrn = Patron.create(
        data=patron2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def patron2_martigny_no_email(
        app,
        roles,
        patron_type_adults_martigny,
        patron2_martigny_data):
    """Create Martigny patron without sending reset password instruction."""
    ptrn = Patron.create(
        data=patron2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Sion, Lib: Sion, System Librarian ----------
@pytest.fixture(scope="module")
def system_librarian_sion_data(data):
    """Load Sion system librarian data."""
    return deepcopy(data.get('ptrn8'))


@pytest.fixture(scope="function")
def system_librarian_sion_data_tmp(data):
    """Load Sion system librarian data scope function."""
    return deepcopy(data.get('ptrn8'))


@pytest.fixture(scope="module")
def system_librarian_sion(
        app,
        roles,
        lib_sion,
        system_librarian_sion_data):
    """Create Sion system librarian record."""
    ptrn = Patron.create(
        data=system_librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def system_librarian_sion_no_email(
        app,
        roles,
        lib_sion,
        system_librarian_sion_data):
    """Create Sion system librarian without sending reset password."""
    ptrn = Patron.create(
        data=system_librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Sion, Lib: Sion, Librarian ----------
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


# ------------ Org: Martigny Patron 2 ----------
@pytest.fixture(scope="module")
def patron2_martigny_data(data):
    """Load Martigny patron data."""
    return deepcopy(data.get('ptrn7'))


@pytest.fixture(scope="module")
def patron2_martigny(
        app,
        roles,
        lib_martigny,
        patron_type_adults_martigny,
        patron2_martigny_data):
    """Create Martigny patron record."""
    ptrn = Patron.create(
        data=patron2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def patron2_martigny_no_email(
        app,
        roles,
        patron_type_adults_martigny,
        patron2_martigny_data):
    """Create Martigny patron without sending reset password instruction."""
    ptrn = Patron.create(
        data=patron2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Sion, Lib: Sion, System Librarian ----------
@pytest.fixture(scope="module")
def system_librarian_sion_data(data):
    """Load Sion system librarian data."""
    return deepcopy(data.get('ptrn8'))


@pytest.fixture(scope="function")
def system_librarian_sion_data_tmp(data):
    """Load Sion system librarian data scope function."""
    return deepcopy(data.get('ptrn8'))


@pytest.fixture(scope="module")
def system_librarian_sion(
        app,
        roles,
        lib_sion,
        system_librarian_sion_data):
    """Create Sion system librarian record."""
    ptrn = Patron.create(
        data=system_librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def system_librarian_sion_no_email(
        app,
        roles,
        lib_sion,
        system_librarian_sion_data):
    """Create Sion system librarian without sending reset password."""
    ptrn = Patron.create(
        data=system_librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Sion, Lib: Sion, Librarian ----------
@pytest.fixture(scope="module")
def librarian_sion_data(data):
    """Load sion librarian data."""
    return deepcopy(data.get('ptrn9'))


@pytest.fixture(scope="module")
def librarian_sion(
        app,
        roles,
        lib_sion,
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
        librarian_sion_data):
    """Create sion librarian without sending reset password instruction."""
    ptrn = Patron.create(
        data=librarian_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Org: Sion Patron 1 ----------
@pytest.fixture(scope="module")
def patron_sion_data(data):
    """Load Sion patron data."""
    return deepcopy(data.get('ptrn10'))


@pytest.fixture(scope="function")
def patron_sion_data_tmp(data):
    """Load Sion patron data scope function."""
    return deepcopy(data.get('ptrn10'))


@pytest.fixture(scope="module")
def patron_sion(
        app,
        roles,
        lib_sion,
        patron_type_grown_sion,
        patron_sion_data):
    """Create Sion patron record."""
    ptrn = Patron.create(
        data=patron_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def patron_sion_no_email(
        app,
        roles,
        patron_type_grown_sion,
        patron_sion_data):
    """Create Sion patron without sending reset password instruction."""
    ptrn = Patron.create(
        data=patron_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


# ------------ Loans: pending loan ----------
@pytest.fixture(scope="module")
def loan_pending_martigny(
        app,
        item_lib_fully,
        loc_public_martigny,
        librarian_martigny_no_email,
        patron2_martigny_no_email,
        circulation_policies):
    """Create loan record with state pending.

    item_lib_fully is requested by patron2_martigny.
    """
    transaction_date = datetime.now(timezone.utc).isoformat()
    item_lib_fully.request(
        patron_pid=patron2_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
        transaction_date=transaction_date,
        pickup_location_pid=loc_public_martigny.pid,
        document_pid=item_lib_fully.replace_refs()['document']['pid']
    )
    flush_index(ItemsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    loan = list(item_lib_fully.get_loans_by_item_pid(
        item_pid=item_lib_fully.pid))[0]
    return loan


@pytest.fixture(scope="module")
def loan_pending_martigny_data(loan_pending_martigny):
    """Load loan data."""
    return deepcopy(loan_pending_martigny)


@pytest.fixture(scope="function")
def loan_pending_martigny_data_tmp(loan_pending_martigny):
    """Load loan data scope function."""
    return deepcopy(loan_pending_martigny)


# ------------ Loans: validated loan ----------
@pytest.fixture(scope="module")
def loan_validated_martigny(
        app,
        document,
        item2_lib_martigny,
        loc_public_martigny,
        item_type_standard_martigny,
        librarian_martigny_no_email,
        patron_martigny_no_email,
        circulation_policies):
    """Request and validate item to a patron.

    item2_lib_martigny is requested and validated to patron_martigny.
    """
    transaction_date = datetime.now(timezone.utc).isoformat()

    item2_lib_martigny.request(
        patron_pid=patron_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
        transaction_date=transaction_date,
        pickup_location_pid=loc_public_martigny.pid,
        document_pid=item2_lib_martigny.replace_refs()['document']['pid']
    )
    flush_index(ItemsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    flush_index(NotificationsSearch.Meta.index)

    loan = list(item2_lib_martigny.get_loans_by_item_pid(
        item_pid=item2_lib_martigny.pid))[0]
    item2_lib_martigny.validate_request(
        pid=loan.pid,
        patron_pid=patron_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
        transaction_date=transaction_date,
        pickup_location_pid=loc_public_martigny.pid,
        document_pid=item2_lib_martigny.replace_refs()['document']['pid']
    )
    flush_index(ItemsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    flush_index(NotificationsSearch.Meta.index)
    loan = list(item2_lib_martigny.get_loans_by_item_pid(
        item_pid=item2_lib_martigny.pid))[0]
    return loan


# ------------ Notifications: availability ----------
@pytest.fixture(scope="module")
def notification_availability_martigny(loan_validated_martigny):
    """Availability notification of martigny."""
    notification = get_availability_notification(loan_validated_martigny)
    return notification


# ------------ Notifications: dummy notification ----------

@pytest.fixture(scope="function")
def dummy_notification(data):
    """Notification data scope function."""
    return deepcopy(data.get('dummy_notif'))
