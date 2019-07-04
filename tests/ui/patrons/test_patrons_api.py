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

"""Patrons Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.patrons.api import Patron, PatronsSearch, \
    patron_id_fetcher


def test_patron_create(app, roles, librarian_martigny_data_tmp,
                       mailbox):
    """Test Patron creation."""
    ds = app.extensions['invenio-accounts'].datastore
    email = librarian_martigny_data_tmp.get('email')
    assert not ds.find_user(email=email)
    assert len(mailbox) == 0
    ptrn = Patron.create(
        librarian_martigny_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    user = ds.find_user(email=email)
    assert user
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(ptrn.get('roles'))
    assert len(mailbox) == 1
    assert ptrn.get('email') in mailbox[0].recipients
    assert ptrn == librarian_martigny_data_tmp
    assert ptrn.get('pid') == '1'

    ptrn = Patron.get_record_by_pid('1')
    assert ptrn == librarian_martigny_data_tmp

    fetched_pid = patron_id_fetcher(ptrn.id, ptrn)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'ptrn'

    # set librarian
    roles = ['librarian']
    ptrn.update({'roles': roles}, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(roles)
    roles = Patron.available_roles
    ptrn.update({'roles': Patron.available_roles}, dbcommit=True)
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
    ptrn = Patron.get_record_by_pid('1')
    assert ptrn is None
    ptrn = Patron.get_record_by_pid('1', with_deleted=True)
    assert ptrn == {}
    assert ptrn.persistent_identifier.pid_value == '1'


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


def test_patron_es_mapping(
        roles, es_clear, lib_martigny, librarian_martigny_data_tmp):
    """Test patron elasticsearch mapping."""
    search = PatronsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)
