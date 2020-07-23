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

"""Common pytest fixtures and plugins."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import mock
import pytest
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, item_record_to_a_specific_loan_state

from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.loans.api import Loan, LoanState
from rero_ils.modules.notifications.api import NotificationsSearch, \
    get_availability_notification
from rero_ils.modules.patron_transactions.api import PatronTransactionsSearch
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


@pytest.fixture(scope="module")
def system_librarian2_martigny_data(data):
    """Load Martigny system librarian data."""
    return deepcopy(data.get('ptrn12'))


@pytest.fixture(scope="function")
def system_librarian2_martigny_data_tmp(data):
    """Load Martigny system librarian data scope function."""
    return deepcopy(data.get('ptrn12'))


@pytest.fixture(scope="module")
def system_librarian2_martigny(
        app,
        roles,
        lib_martigny,
        system_librarian2_martigny_data):
    """Create Martigny system librarian record."""
    ptrn = Patron.create(
        data=system_librarian2_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def system_librarian2_martigny_no_email(
        app,
        roles,
        lib_martigny,
        system_librarian2_martigny_data):
    """Create Martigny system librarian without sending reset password."""
    ptrn = Patron.create(
        data=system_librarian2_martigny_data,
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
    ptrn = Patron.get_record_by_pid(librarian_martigny_data['pid'])
    if ptrn:
        ptrn = ptrn.update(
            data=librarian_martigny_data,
            dbcommit=True,
            reindex=True
        )
    else:
        ptrn = Patron.create(
            data=librarian_martigny_data,
            delete_pid=False,
            dbcommit=True,
            reindex=True
        )
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
    ptrn = Patron.get_record_by_pid(patron_martigny_data.get('pid'))
    if ptrn:
        ptrn = ptrn.update(
            data=patron_martigny_data,
            dbcommit=True,
            reindex=True
        )
    else:
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


# ------------ Org: Martigny Patron 3 (blocked) ----------
@pytest.fixture(scope="module")
def patron3_martigny_blocked_data(data):
    """Load Martigny blocked patron data."""
    return deepcopy(data.get('ptrn11'))


@pytest.fixture(scope="module")
def patron3_martigny_blocked(
        app,
        roles,
        lib_martigny,
        patron_type_adults_martigny,
        patron3_martigny_blocked_data):
    """Create Martigny patron record."""
    ptrn = Patron.create(
        data=patron3_martigny_blocked_data,
        delete_pid=True,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def patron3_martigny_blocked_no_email(
        app,
        roles,
        patron_type_adults_martigny,
        patron3_martigny_blocked_data):
    """Create Martigny patron without sending reset password instruction."""
    ptrn = Patron.create(
        data=patron3_martigny_blocked_data,
        delete_pid=True,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
def patron4_martigny_data(data):
    """Load Martigny patron data."""
    return deepcopy(data.get('ptrn12'))


@pytest.fixture(scope="module")
def patron4_martigny(
        app,
        roles,
        lib_martigny,
        patron_type_adults_martigny,
        patron4_martigny_data):
    """Create Martigny patron record."""
    ptrn = Patron.create(
        data=patron4_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronsSearch.Meta.index)
    return ptrn


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def patron4_martigny_no_email(
        app,
        roles,
        patron_type_adults_martigny,
        patron4_martigny_data):
    """Create Martigny patron without sending reset password instruction."""
    ptrn = Patron.create(
        data=patron4_martigny_data,
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
        lib_sion,
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


# ------------ Patron Transactions: Lib Martigny overdue scenario ----------
@pytest.fixture(scope="module")
def loan_overdue_martigny(
        app,
        document,
        item4_lib_martigny,
        loc_public_martigny,
        item_type_standard_martigny,
        librarian_martigny_no_email,
        patron_martigny_no_email,
        circulation_policies):
    """Checkout an item to a patron.

    item4_lib_martigny is overdue.
    """
    transaction_date = datetime.now(timezone.utc).isoformat()

    item4_lib_martigny.checkout(
        patron_pid=patron_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
        transaction_date=transaction_date,
        document_pid=item4_lib_martigny.replace_refs()['document']['pid']
    )
    flush_index(ItemsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    loan = Loan.get_record_by_pid(
        item4_lib_martigny.get_loan_pid_with_item_on_loan(
            item4_lib_martigny.pid))
    end_date = datetime.now(timezone.utc) - timedelta(days=25)
    loan['end_date'] = end_date.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    return loan


@pytest.fixture(scope="module")
def notification_overdue_martigny(
        app,
        loan_overdue_martigny):
    """Create an overdue notification for an overdue loan."""
    notification = loan_overdue_martigny.create_notification(
        notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    flush_index(PatronTransactionsSearch.Meta.index)

    return notification


@pytest.fixture(scope="module")
def patron_transaction_overdue_martigny(
        app,
        notification_overdue_martigny):
    """Return an overdue patron transaction for an overdue notification."""
    records = list(notification_overdue_martigny.patron_transactions)

    return records[0]


@pytest.fixture(scope="module")
def patron_transaction_overdue_event_martigny(
        app,
        patron_transaction_overdue_martigny):
    """Return overdue events for patron transaction for a notification."""
    for event in patron_transaction_overdue_martigny.events:
        return event


@pytest.fixture(scope="module")
def patron_transaction_overdue_events_martigny(
        app,
        patron_transaction_overdue_martigny):
    """Return overdue events for patron transaction for a notification."""
    return patron_transaction_overdue_martigny.events


# ------------ Patron Transactions: Lib Saxon overdue scenario ----------


@pytest.fixture(scope="module")
def loan_overdue_saxon(
        app,
        document,
        item2_lib_saxon,
        loc_public_martigny,
        item_type_standard_martigny,
        librarian_martigny_no_email,
        patron_martigny_no_email,
        circulation_policies):
    """Checkout an item to a patron.

    item2_lib_saxon is overdue.
    """
    transaction_date = datetime.now(timezone.utc).isoformat()

    item2_lib_saxon.checkout(
        patron_pid=patron_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
        transaction_date=transaction_date,
        document_pid=item2_lib_saxon.replace_refs()['document']['pid']
    )
    flush_index(ItemsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    loan = Loan.get_record_by_pid(
        item2_lib_saxon.get_loan_pid_with_item_on_loan(
            item2_lib_saxon.pid))
    end_date = datetime.now(timezone.utc) - timedelta(days=25)
    loan['end_date'] = end_date.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    return loan


@pytest.fixture(scope="module")
def notification_overdue_saxon(
        app,
        loan_overdue_saxon):
    """Create an overdue notification for an overdue loan."""
    notification = loan_overdue_saxon.create_notification(
        notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    flush_index(PatronTransactionsSearch.Meta.index)

    return notification


@pytest.fixture(scope="module")
def patron_transaction_overdue_saxon(
        app,
        notification_overdue_saxon):
    """Return an overdue patron transaction for an overdue notification."""
    records = list(notification_overdue_saxon.patron_transactions)
    return records[0]


@pytest.fixture(scope="module")
def patron_transaction_overdue_event_saxon(
        app,
        patron_transaction_overdue_saxon):
    """Return overdue events for patron transaction for a notification."""
    for event in patron_transaction_overdue_saxon.events:
        return event


@pytest.fixture(scope="module")
def patron_transaction_overdue_saxon_data(data):
    """Load Martigny patron transaction martigny data."""
    return deepcopy(data.get('dummy_patron_transaction'))


@pytest.fixture(scope="module")
def patron_transaction_overdue_event_saxon_data(data):
    """Load Martigny patron transaction martigny data."""
    return deepcopy(data.get('dummy_patron_transaction_event'))


# ------------ Loans and items for circulation actions ----------

@pytest.fixture(scope="module")
def item_on_shelf_martigny_patron_and_loan_pending(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies,):
    """Creates an item on_shelf requested by a patron.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.PENDING,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item2_on_shelf_martigny_patron_and_loan_pending(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies,):
    """Creates an item on_shelf requested by a patron.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.PENDING,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item_at_desk_martigny_patron_and_loan_at_desk(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item with a validated pending request.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the validated pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item2_at_desk_martigny_patron_and_loan_at_desk(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item with a validated pending request.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the validated pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item3_at_desk_martigny_patron_and_loan_at_desk(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item with a validated pending request.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the validated pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item4_at_desk_martigny_patron_and_loan_at_desk(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item with a validated pending request.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the validated pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item5_at_desk_martigny_patron_and_loan_at_desk(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item with a validated pending request.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the validated pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item_on_shelf_fully_patron_and_loan_pending(
        app,
        librarian_martigny_no_email,
        item_lib_fully, loc_public_fully,
        patron_martigny_no_email, circulation_policies,):
    """Creates an item on_shelf requested by a patron.

    :return item: the created or copied item.
    :return patron: the patron placed the request.
    :return loan: the pending loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_fully,
        loan_state=LoanState.PENDING,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item_on_loan_martigny_patron_and_loan_on_loan(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item on_loan.

    :return item: the created or copied item.
    :return patron: the patron checked-out the item for.
    :return loan: the ITEM_ON_LOAN loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item2_on_loan_martigny_patron_and_loan_on_loan(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item on_loan.

    :return item: the created or copied item.
    :return patron: the patron checked-out the item for.
    :return loan: the ITEM_ON_LOAN loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item3_on_loan_martigny_patron_and_loan_on_loan(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item on_loan.

    :return item: the created or copied item.
    :return patron: the patron checked-out the item for.
    :return loan: the ITEM_ON_LOAN loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item4_on_loan_martigny_patron_and_loan_on_loan(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item on_loan.

    :return item: the created or copied item.
    :return patron: the patron checked-out the item for.
    :return loan: the ITEM_ON_LOAN loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item5_on_loan_martigny_patron_and_loan_on_loan(
        app,
        librarian_martigny_no_email,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item on_loan.

    :return item: the created or copied item.
    :return patron: the patron checked-out the item for.
    :return loan: the ITEM_ON_LOAN loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item_on_loan_fully_patron_and_loan_on_loan(
        app,
        librarian_martigny_no_email,
        item_lib_fully, loc_public_fully,
        patron_martigny_no_email, circulation_policies):
    """Creates an item on_loan.

    :return item: the created or copied item.
    :return patron: the patron checked-out the item for.
    :return loan: the ITEM_ON_LOAN loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_fully,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item_in_transit_martigny_patron_and_loan_for_pickup(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit for pickup.

    :return item: the created or copied item.
    :return patron: the patron requested the item.
    :return loan: the ITEM_IN_TRANSIT_FOR_PICKUP loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item2_in_transit_martigny_patron_and_loan_for_pickup(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit for pickup.

    :return item: the created or copied item.
    :return patron: the patron requested the item.
    :return loan: the ITEM_IN_TRANSIT_FOR_PICKUP loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item3_in_transit_martigny_patron_and_loan_for_pickup(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit for pickup.

    :return item: the created or copied item.
    :return patron: the patron requested the item.
    :return loan: the ITEM_IN_TRANSIT_FOR_PICKUP loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item_in_transit_martigny_patron_and_loan_to_house(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit to house.

    :return item: the created or copied item.
    :return patron: the patron who returned this item.
    :return loan: the ITEM_IN_TRANSIT_TO_HOUSE loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item2_in_transit_martigny_patron_and_loan_to_house(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit to house.

    :return item: the created or copied item.
    :return patron: the patron who returned this item.
    :return loan: the ITEM_IN_TRANSIT_TO_HOUSE loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item3_in_transit_martigny_patron_and_loan_to_house(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit to house.

    :return item: the created or copied item.
    :return patron: the patron who returned this item.
    :return loan: the ITEM_IN_TRANSIT_TO_HOUSE loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item4_in_transit_martigny_patron_and_loan_to_house(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit to house.

    :return item: the created or copied item.
    :return patron: the patron who returned this item.
    :return loan: the ITEM_IN_TRANSIT_TO_HOUSE loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item5_in_transit_martigny_patron_and_loan_to_house(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit to house.

    :return item: the created or copied item.
    :return patron: the patron who returned this item.
    :return loan: the ITEM_IN_TRANSIT_TO_HOUSE loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan


@pytest.fixture(scope="module")
def item6_in_transit_martigny_patron_and_loan_to_house(
        app,
        librarian_martigny_no_email, loc_public_fully,
        item_lib_martigny, loc_public_martigny,
        patron_martigny_no_email, circulation_policies):
    """Creates an item in_transit to house.

    :return item: the created or copied item.
    :return patron: the patron who returned this item.
    :return loan: the ITEM_IN_TRANSIT_TO_HOUSE loan.
    """
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)
    return item, patron_martigny_no_email, loan
