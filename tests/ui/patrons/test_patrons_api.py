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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.patrons.api import Patron, PatronsSearch, \
    patron_id_fetcher


def test_patron_create(base_app, roles, user_librarian_data_tmp,
                       mailbox):
    """Test Patron creation."""
    ds = base_app.extensions['invenio-accounts'].datastore
    email = user_librarian_data_tmp.get('email')
    assert not ds.find_user(email=email)
    assert len(mailbox) == 0
    ptrn = Patron.create(user_librarian_data_tmp, dbcommit=True)
    user = ds.find_user(email=email)
    assert user
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(ptrn.get('roles'))
    assert len(mailbox) == 1
    assert ptrn.get('email') in mailbox[0].recipients
    assert ptrn == user_librarian_data_tmp
    assert ptrn.get('pid') == '1'

    ptrn = Patron.get_record_by_pid('1')
    assert ptrn == user_librarian_data_tmp

    fetched_pid = patron_id_fetcher(ptrn.id, ptrn)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'ptrn'

    roles = ['librarian']
    ptrn.update({'roles': roles}, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(roles)
    del ptrn['roles']
    ptrn.update({}, dbcommit=True)
    assert not user.roles
    roles = Patron.available_roles
    ptrn.update({'roles': Patron.available_roles}, dbcommit=True)
    user_roles = [r.name for r in user.roles]
    assert set(user_roles) == set(Patron.available_roles)
    ptrn.delete()
    user = ds.find_user(email=email)
    assert user
    assert not user.roles
    assert len(mailbox) == 1
    ptrn = Patron.get_record_by_pid('1')
    assert ptrn is None
    ptrn = Patron.get_record_by_pid('1', with_deleted=True)
    assert ptrn == {}
    assert ptrn.persistent_identifier.pid_value == '1'


def test_patron_es_mapping(
        roles, es_clear, library, patron_type, user_librarian_data_tmp):
    """."""
    search = PatronsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Patron.create(user_librarian_data_tmp, dbcommit=True, reindex=True)
    assert mapping == get_mapping(search.Meta.index)


def test_get_patron(user_librarian):
    """."""
    patron = user_librarian
    assert Patron.get_patron_by_email(patron.get('email')) == patron
    assert not Patron.get_patron_by_email('not exists')
    assert Patron.get_patron_by_barcode('2050124311') == patron
    assert not Patron.get_patron_by_barcode('not exists')

    class user:
        email = patron.get('email')
    assert Patron.get_patron_by_user(user) == patron
