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

from copy import deepcopy

import pytest
from invenio_accounts.models import User
from jsonschema.exceptions import ValidationError

from rero_ils.modules.patrons.api import Patron, PatronsSearch, \
    patron_id_fetcher
from rero_ils.modules.patrons.models import CommunicationChannel
from rero_ils.modules.patrons.utils import create_user_from_data
from rero_ils.modules.users.models import UserRole


def test_patron_extended_validation(app, patron_martigny,
                                    patron_martigny_data_tmp, patron2_martigny,
                                    patron_sion, patron_sion_data_tmp):
    """Test that a patron barcode must be unique within organisation"""
    ds = app.extensions['invenio-accounts'].datastore

    # check that we cannot create a patron with an existing barcode
    with pytest.raises(ValidationError) as err:
        created_patron_martigny = create_user_from_data(
            patron_martigny_data_tmp
            )
        Patron.create(
            created_patron_martigny,
            delete_pid=True
        )
    assert 'already taken' in str(err)

    # check if resource update doesn't trigger validation error on own barcode
    patron_martigny['patron']['barcode'].append('duplicate')
    assert patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)

    # check that we cannot update a patron to an existing barcode
    patron2_martigny['patron']['barcode'].append('duplicate')
    with pytest.raises(ValidationError) as err:
        patron2_martigny.update(patron2_martigny)
    assert 'already taken' in str(err)

    # check that we can create a patron even with existing barcode in another
    # organisation
    patron_sion_barcode = patron_sion['patron']['barcode']
    created_patron_sion = \
        create_user_from_data(patron_sion_data_tmp)
    created_patron_sion['patron']['barcode']\
        = [patron_martigny['patron']['barcode'][0]]
    assert (created_user := Patron.create(created_patron_sion, dbcommit=True,
                                          reindex=True, delete_pid=True))

    # check that we can update a patron with existing barcode in another
    # organisation
    patron_sion['patron']['barcode'] = ['duplicate']
    assert patron_sion.update(patron_sion)

    # clean up fixtures
    patron_sion['patron']['barcode'] = patron_sion_barcode
    patron_martigny['patron']['barcode'].pop()
    patron2_martigny['patron']['barcode'].pop()
    patron_sion.update(
        patron_sion, commit=True, dbcommit=True, reindex=True)
    patron_martigny.update(
        patron_martigny, commit=True, dbcommit=True, reindex=True)
    patron2_martigny.update(
        patron2_martigny, commit=True, dbcommit=True, reindex=True)

    # clean up created user
    created_user.delete(True, True, True)
    user = created_user.user
    ds.delete_user(user)


def test_patron_create(app, roles, lib_martigny, librarian_martigny_data_tmp,
                       patron_type_adults_martigny, mailbox):
    """Test Patron creation."""
    ds = app.extensions['invenio-accounts'].datastore
    email = librarian_martigny_data_tmp.get('email')

    l_martigny_data_tmp = librarian_martigny_data_tmp
    librarian_martigny_data_tmp = create_user_from_data(
        librarian_martigny_data_tmp)
    # wrong_librarian_martigny_data_tmp = deepcopy(librarian_martigny_data_tmp)
    # wrong_librarian_martigny_data_tmp.pop('first_name')
    # with pytest.raises(ValidationError):
    #     ptrn = Patron.create(
    #         wrong_librarian_martigny_data_tmp,
    #         dbcommit=True,
    #         delete_pid=True
    #     )

    wrong_librarian_martigny_data_tmp = deepcopy(librarian_martigny_data_tmp)
    wrong_librarian_martigny_data_tmp.pop('libraries')
    with pytest.raises(ValidationError) as err:
        Patron.create(
            wrong_librarian_martigny_data_tmp,
            dbcommit=True,
            delete_pid=True
        )
    assert str(err.value) == 'Missing libraries'

    wrong_librarian_martigny_data_tmp = deepcopy(librarian_martigny_data_tmp)
    wrong_librarian_martigny_data_tmp.setdefault('patron', {
        'expiration_date': '2023-10-07',
        'barcode': ['2050124311'],
        'type': {
          '$ref': 'https://bib.rero.ch/api/patron_types/ptty2'
        },
        'communication_channel': CommunicationChannel.EMAIL,
        'communication_language': 'ita'
    })
    wrong_librarian_martigny_data_tmp['patron']['subscriptions'] = [{
        'start_date': '2000-01-01',
        'end_date': '2001-01-01',
        'patron_type': {'$ref': 'https://bib.rero.ch/api/patron_types/xxx'},
        'patron_transaction': {
            '$ref': 'https://bib.rero.ch/api/patron_transactions/xxx'
        },
    }]
    with pytest.raises(ValidationError):
        Patron.create(
            wrong_librarian_martigny_data_tmp,
            dbcommit=True,
            delete_pid=True
        )

    # no data has been created
    assert len(mailbox) == 0
    # assert User.query.count() == 0
    # assert UserProfile.query.count() == 0

    ptrn = Patron.create(
        librarian_martigny_data_tmp,
        dbcommit=True,
        delete_pid=False
    )
    user = User.query.filter_by(id=ptrn.get('user_id')).first()
    assert user and user.active
    for field in ['first_name', 'last_name', 'street', 'postal_code', 'city',
                  'home_phone']:
        assert user.user_profile.get(field) == l_martigny_data_tmp.get(field)
    assert user.username == l_martigny_data_tmp.get('username')
    assert user.user_profile.get('birth_date') == \
           l_martigny_data_tmp.get('birth_date')
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(ptrn.get('roles'))
    # TODO: make these checks during the librarian POST creation
    # assert len(mailbox) == 1
    # assert re.search(r'localhost/lost-password', mailbox[0].body)
    # assert re.search(
    #     r'Someone requested that the password' +
    #     ' for your RERO ID account be reset.', mailbox[0].body
    # )
    # assert re.search(
    #     r'Best regards', mailbox[0].body
    # )
    # assert ptrn.get('email') in mailbox[0].recipients
    librarian_martigny_data_tmp['user_id'] = ptrn.user.id
    assert ptrn == librarian_martigny_data_tmp

    ptrn = Patron.get_record_by_pid(ptrn.pid)
    # assert ptrn == librarian_martigny_data_tmp

    fetched_pid = patron_id_fetcher(ptrn.id, ptrn)
    assert fetched_pid.pid_value == ptrn.pid
    assert fetched_pid.pid_type == 'ptrn'

    # set librarian
    roles = UserRole.LIBRARIAN_ROLES
    ptrn.update({'roles': roles}, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(roles)
    data = {
        'roles': UserRole.ALL_ROLES,
        'patron': {
            'expiration_date': '2023-10-07',
            'barcode': ['2050124311'],
            'type': {
              '$ref': 'https://bib.rero.ch/api/patron_types/ptty2'
            },
            'communication_channel': CommunicationChannel.EMAIL,
            'communication_language': 'ita'
        }
    }
    ptrn.update(data, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(UserRole.ALL_ROLES)

    # remove patron
    ptrn.delete(False, True, True)
    # user still exist in the invenio db
    user = ds.find_user(email=email)
    assert user
    # all roles have been removed
    assert not user.roles
    # assert len(mailbox) == 1
    # patron does not exists anymore
    ptrn = Patron.get_record_by_pid('ptrn2')
    assert ptrn is None
    ptrn = Patron.get_record_by_pid('ptrn2', with_deleted=True)
    assert ptrn == {}
    assert ptrn.persistent_identifier.pid_value == 'ptrn2'
    # remove patron
    ptrn.delete(True, True, True)
    # clean up the user
    ds.delete_user(user)


@pytest.mark.skip(reason="no way of currently testing this")
def test_patron_create_without_email(app, roles, patron_type_children_martigny,
                                     patron_martigny_data_tmp, mailbox):
    """Test Patron creation without an email."""
    patron_martigny_data_tmp = deepcopy(patron_martigny_data_tmp)

    # no data has been created
    mailbox.clear()
    del patron_martigny_data_tmp['email']

    patron_martigny_data_tmp = \
        create_user_from_data(patron_martigny_data_tmp)
    from rero_ils.modules.users.api import User
    patron_martigny_data_tmp = User.remove_fields(patron_martigny_data_tmp)

    # communication channel require at least one email
    patron_martigny_data_tmp['patron']['communication_channel'] = 'email'
    with pytest.raises(ValidationError):
        Patron.create(
            patron_martigny_data_tmp,
            dbcommit=True,
            delete_pid=True
        )

    # create a patron without email
    patron_martigny_data_tmp['patron']['communication_channel'] = \
        CommunicationChannel.MAIL
    ptrn = Patron.create(
        patron_martigny_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    # user has been created
    user = User.query.filter_by(id=ptrn.get('user_id')).first()
    assert user
    assert not user.email
    assert user == ptrn.user
    assert user.active
    assert len(mailbox) == 0

    # # add an email of a non existing user
    # patron_martigny_data_tmp['email'] = 'test@test.ch'
    # ptrn.replace(
    #     data=patron_martigny_data_tmp,
    #     dbcommit=True
    # )
    # # the user remains the same
    # assert user == ptrn.user
    # assert user.email == patron_martigny_data_tmp['email']
    # assert user.active
    # assert len(mailbox) == 0

    # # update with a new email in the system
    # patron_martigny_data_tmp['email'] = 'test@test1.ch'
    # ptrn.replace(
    #     data=patron_martigny_data_tmp,
    #     dbcommit=True
    # )
    # # the user remains the same
    # assert user == ptrn.user
    # assert user.email == patron_martigny_data_tmp['email']
    # assert user.active
    # assert len(mailbox) == 0

    # # remove the email
    # del patron_martigny_data_tmp['email']
    # ptrn.replace(
    #     data=patron_martigny_data_tmp,
    #     dbcommit=True
    # )
    # assert user == ptrn.user
    # assert not user.email
    # assert user.active
    # assert len(mailbox) == 0

    # # create a new invenio user in the system
    # rero_id_user = create_test_user(email='reroid@test.com', active=True)

    # # update the patron with the email of the freshed create invenio user
    # patron_martigny_data_tmp['email'] = 'reroid@test.com'
    # patron_martigny_data_tmp['username'] = 'reroid'
    # ptrn.replace(
    #     data=patron_martigny_data_tmp,
    #     dbcommit=True
    # )
    # # the user linked with the patron has been changed
    # assert rero_id_user == ptrn.user
    # # the username is updated on both user profile and patron
    # assert rero_id_user.profile.username == ptrn.get('username') == 'reroid'

    # clean up created users
    ds = app.extensions['invenio-accounts'].datastore
    ds.delete_user(user)


def test_patron_properties(
    org_martigny, patron_martigny, librarian_martigny, patron2_martigny,
    lib_martigny, system_librarian_martigny
):
    """Test patron properties methods."""

    # TEST `organisation.pid`
    search = PatronsSearch()
    librarian = next(search.filter('term', pid=librarian_martigny.pid).scan())
    patron = next(search.filter('term', pid=patron_martigny.pid).scan())
    assert patron.organisation.pid == org_martigny.pid
    assert librarian.organisation.pid == org_martigny.pid

    # TEST `manageable_library_pids`
    assert librarian_martigny.manageable_library_pids == [lib_martigny.pid]
    assert system_librarian_martigny.manageable_library_pids == \
           org_martigny.get_libraries_pids()

    # TEST `blocked`
    patron = Patron.get_patron_by_email(patron_martigny.dumps().get('email'))
    assert patron.patron.get('blocked') is False
    # TEST `blocked` is absent
    patron = Patron.get_patron_by_email(patron2_martigny.dumps().get('email'))
    assert 'blocked' not in patron

    # TEST `profile_url`
    assert org_martigny.get('code') in patron2_martigny.profile_url


def test_get_patron(patron_martigny):
    """Test patron retrieval."""
    patron = patron_martigny
    assert Patron.get_patron_by_email(patron.dumps().get('email')) == patron
    assert not Patron.get_patron_by_email('not exists')
    assert Patron.get_patron_by_barcode(
        patron.patron.get('barcode')[0]) == patron
    assert not Patron.get_patron_by_barcode('not exists')
    assert Patron.get_patrons_by_user(patron.user)[0] == patron

    class user:
        pass
    assert not Patron.get_patrons_by_user(user)


def test_get_patrons_by_user(patron_martigny):
    """Test patrons retrieval."""
    patrons = Patron.get_patrons_by_user(patron_martigny.user)
    assert type(patrons) is list
    assert patron_martigny == patrons[0]


def test_user_librarian_can_delete(librarian_martigny):
    """Test can delete a librarian."""
    can, reasons = librarian_martigny.can_delete
    assert can and reasons == {}


def test_get_patron_for_organisation(
    patron_martigny, patron_sion, org_martigny, org_sion
):
    """Test get patron_pid for organisation."""

    pids = Patron.get_all_pids_for_organisation(org_martigny.pid)
    assert list(pids)
    pids = Patron.get_all_pids_for_organisation(org_sion.pid)
    assert list(pids)


def test_patron_multiple(patron_sion_multiple, patron2_martigny, lib_martigny):
    """Test changing roles for multiple patron accounts."""
    assert patron2_martigny.user == patron_sion_multiple.user
    data = dict(patron_sion_multiple)
    patron2_roles = {r.name for r in patron2_martigny.user.roles}
    patron_and_librarian_roles = UserRole.LIBRARIAN_ROLES + [UserRole.PATRON]
    assert all(r in patron_and_librarian_roles for r in patron2_roles)
    data['roles'] = [UserRole.PATRON]
    del data['libraries']
    patron_sion_multiple.update(data, dbcommit=True, reindex=True)
    assert patron2_martigny.user.roles == [UserRole.PATRON]
    assert Patron.get_record_by_pid(patron_sion_multiple.pid).get('roles') == \
        [UserRole.PATRON]
    assert Patron.get_record_by_pid(patron2_martigny.pid).get('roles') == \
        [UserRole.PATRON]
