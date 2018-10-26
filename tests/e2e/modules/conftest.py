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

"""Pytest fixtures and plugins for the UI application."""

from __future__ import absolute_import, print_function

import pytest
from flask_security.confirmable import confirm_user
from flask_security.utils import hash_password
from invenio_search import current_search
from werkzeug.local import LocalProxy

from rero_ils.modules.patrons.api import Patron


def es_flush_and_refresh():
    """Elasticsearch flush and refresh indexes."""
    for index in current_search.mappings:
        current_search.flush_and_refresh(index)


def create_roles(app):
    """Create roles."""
    datastore = LocalProxy(
        lambda: app.extensions['security'].datastore
    )
    roles = ['patrons', 'staff', 'cataloguer']
    for role in roles:
        if not datastore.find_role(role):
            datastore.create_role(name=role)
    datastore.commit()


def test_user(app, name='name', is_patron=False, is_staff=False,
              library_pid='1', barcode='2050124311'):
    """Create test user."""
    create_roles(app)

    datastore = LocalProxy(
        lambda: app.extensions['security'].datastore
    )

    email = '{name}@rero.ch'.format(name=name)
    user = datastore.create_user(
        email=email,
        active=True,
        password=hash_password(name),
    )
    datastore.commit()
    user = datastore.find_user(email=email)
    confirm_user(user)
    datastore.commit()

    patron_data = {
        '$schema':
            'https://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '0',
        'first_name': name,
        'last_name': name,
        'birth_date': '1111-11-11',
        'email': email,
        'street': 'street 11',
        'postal_code': '1111',
        'city': 'City',
        'library_pid': library_pid,
        'is_patron': is_patron,
        'is_staff': is_staff,
    }
    if is_patron:
        patron_data['barcode'] = barcode
    patron = Patron.create(
        patron_data,
        dbcommit=True,
        reindex=True
    )
    if is_patron:
        patron.add_role(role_name='patrons')
    if is_staff:
        patron.add_role(role_name='cataloguer')
        patron.add_role(role_name='staff')
    patron.dbcommit()
    patron.reindex()
    user.patron = patron
    user.password_plaintext = name
    es_flush_and_refresh()
    return user


@pytest.fixture(scope='module')
def user_staff_patron(app):
    """Create staff patron user."""
    yield test_user(app, name='staff_patron',
                    is_patron=True, is_staff=True)


@pytest.fixture(scope='module')
def user_staff(app):
    """Create staff user."""
    yield test_user(app, name='staff', is_staff=True)


@pytest.fixture(scope='module')
def user_patron(app):
    """Create patron user."""
    yield test_user(app, name='patron', is_patron=True)
