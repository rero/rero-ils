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

"""Patrons Record tests."""

from __future__ import absolute_import, print_function

import re
from copy import deepcopy
from datetime import datetime

import pytest
from invenio_accounts.models import User
from invenio_userprofiles import UserProfile
from jsonschema.exceptions import ValidationError

from rero_ils.modules.errors import RecordValidationError
from rero_ils.modules.patrons.api import Patron, PatronsSearch, \
    patron_id_fetcher


def test_patron_create(app, roles, lib_martigny, librarian_martigny_data_tmp,
                       patron_type_adults_martigny, mailbox):
    """Test Patron creation."""
    ds = app.extensions['invenio-accounts'].datastore
    email = librarian_martigny_data_tmp.get('email')

    # sanity checks
    assert len(mailbox) == 0
    assert User.query.count() == 0
    assert UserProfile.query.count() == 0

    wrong_librarian_martigny_data_tmp = deepcopy(librarian_martigny_data_tmp)
    wrong_librarian_martigny_data_tmp.pop('first_name')
    with pytest.raises(ValidationError):
        ptrn = Patron.create(
            wrong_librarian_martigny_data_tmp,
            dbcommit=True,
            delete_pid=True
        )

    wrong_librarian_martigny_data_tmp = deepcopy(librarian_martigny_data_tmp)
    wrong_librarian_martigny_data_tmp.pop('library')
    with pytest.raises(RecordValidationError):
        ptrn = Patron.create(
            wrong_librarian_martigny_data_tmp,
            dbcommit=True,
            delete_pid=True
        )

    wrong_librarian_martigny_data_tmp = deepcopy(librarian_martigny_data_tmp)
    wrong_librarian_martigny_data_tmp['subscriptions'] = [{
        'start_date': '2000-01-01',
        'end_date': '2001-01-01',
        'patron_type': {'$ref': 'https://ils.rero.ch/api/patron_types/xxx'},
        'patron_transaction': {
            '$ref': 'https://ils.rero.ch/api/patron_transactions/xxx'
        },
    }]
    with pytest.raises(RecordValidationError):
        ptrn = Patron.create(
            wrong_librarian_martigny_data_tmp,
            dbcommit=True,
            delete_pid=True
        )

    # no data has been created
    assert len(mailbox) == 0
    assert User.query.count() == 0
    assert UserProfile.query.count() == 0

    ptrn = Patron.create(
        librarian_martigny_data_tmp,
        dbcommit=True,
        delete_pid=False
    )
    user = User.query.filter_by(id=ptrn.get('user_id')).first()
    assert user
    assert user.active
    for field in [
        'first_name', 'last_name', 'street', 'postal_code', 'city', 'username',
        'phone'
    ]:
        assert getattr(user.profile, field) == librarian_martigny_data_tmp.get(
            field)
    user.profile.birth_date == datetime.strptime(
        librarian_martigny_data_tmp.get('birth_date'), '%Y-%m-%d')
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(ptrn.get('roles'))
    assert len(mailbox) == 1
    assert re.search(r'localhost/lost-password', mailbox[0].body)
    assert ptrn.get('email') in mailbox[0].recipients
    librarian_martigny_data_tmp['user_id'] = 1
    assert ptrn == librarian_martigny_data_tmp
    assert ptrn.get('pid') == 'ptrn2'

    ptrn = Patron.get_record_by_pid('ptrn2')
    # assert ptrn == librarian_martigny_data_tmp

    fetched_pid = patron_id_fetcher(ptrn.id, ptrn)
    assert fetched_pid.pid_value == 'ptrn2'
    assert fetched_pid.pid_type == 'ptrn'

    # set librarian
    roles = ['librarian']
    ptrn.update({'roles': roles}, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(roles)
    roles = Patron.available_roles
    data = {
        'roles': Patron.available_roles,
        'patron_type': {'$ref': 'https://ils.rero.ch/api/patron_types/ptty2'}
    }
    ptrn.update(data, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(Patron.available_roles)

    # remove patron
    ptrn.delete()
    # user still exist in the invenio db
    user = ds.find_user(email=email)
    assert user
    # all roles has been removed
    assert not user.roles
    assert len(mailbox) == 1
    # patron does not exists anymore
    ptrn = Patron.get_record_by_pid('ptrn2')
    assert ptrn is None
    ptrn = Patron.get_record_by_pid('ptrn2', with_deleted=True)
    assert ptrn == {}
    assert ptrn.persistent_identifier.pid_value == 'ptrn2'
    # clean up the user
    ds.delete_user(user)


def test_patron_organisation_pid(org_martigny, patron_martigny_no_email,
                                 librarian_martigny_no_email):
    """Test organisation pid has been added during the indexing."""
    search = PatronsSearch()
    librarian = next(search.filter('term',
                                   pid=librarian_martigny_no_email.pid).scan())
    patron = next(search.filter('term',
                                pid=patron_martigny_no_email.pid).scan())
    assert patron.organisation.pid == org_martigny.pid
    assert librarian.organisation.pid == org_martigny.pid


def test_get_patron(patron_martigny_no_email):
    """Test patron retrieval."""
    patron = patron_martigny_no_email
    assert Patron.get_patron_by_email(patron.get('email')) == patron
    assert not Patron.get_patron_by_email('not exists')
    assert Patron.get_patron_by_barcode(patron.get('barcode')) == patron
    assert not Patron.get_patron_by_barcode('not exists')

    class user:
        email = patron.get('email')
    assert Patron.get_patron_by_user(user) == patron


def test_user_librarian_can_delete(librarian_martigny):
    """Test can delete a librarian."""
    assert librarian_martigny.get_links_to_me() == {}
    assert librarian_martigny.can_delete


def test_get_patron_blocked_field(patron_martigny_no_email):
    """Test patron blocked field retrieval."""
    patron = Patron.get_patron_by_email(patron_martigny_no_email.get('email'))
    assert 'blocked' in patron
    assert patron.get('blocked', {}) is False


def test_get_patron_blocked_field_absent(patron2_martigny_no_email):
    """Test patron blocked field retrieval."""
    patron = Patron.get_patron_by_email(patron2_martigny_no_email.get('email'))
    assert 'blocked' not in patron


def test_get_reachable_roles():
    """Test get roles covered by the given role."""
    roles = Patron.get_reachable_roles(Patron.ROLE_SYSTEM_LIBRARIAN)
    assert len(roles) == 2
    assert Patron.ROLE_LIBRARIAN in roles
    assert Patron.ROLE_SYSTEM_LIBRARIAN in roles

    roles = Patron.get_reachable_roles('unknown_role')
    assert not roles


def test_get_all_roles_for_role():
    """Test get roles covering by roles hierarchy."""
    roles = Patron.get_all_roles_for_role(Patron.ROLE_PATRON)
    assert len(roles) == 1
    assert Patron.ROLE_PATRON in roles

    roles = Patron.get_all_roles_for_role(Patron.ROLE_SYSTEM_LIBRARIAN)
    assert len(roles) == 1
    assert Patron.ROLE_SYSTEM_LIBRARIAN in roles

    roles = Patron.get_all_roles_for_role(Patron.ROLE_LIBRARIAN)
    assert len(roles) == 2
    assert Patron.ROLE_LIBRARIAN in roles
    assert Patron.ROLE_SYSTEM_LIBRARIAN in roles


def test_get_patron_for_organisation(patron_martigny_no_email,
                                     patron_sion_no_email,
                                     org_martigny, org_sion):
    """Test get patron_pid for organisation."""

    pids = Patron.get_all_pids_for_organisation(org_martigny.pid)
    assert len(list(pids)) > 0
    pids = Patron.get_all_pids_for_organisation(org_sion.pid)
    assert len(list(pids)) > 0
