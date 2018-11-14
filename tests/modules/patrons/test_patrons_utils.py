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

"""Utils tests."""

from __future__ import absolute_import, print_function

from flask_security.utils import hash_password
from invenio_accounts.models import User
from werkzeug.local import LocalProxy

from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.utils import save_patron
from rero_ils.modules.patrons_types.api import PatronType


def test_save_patron(app, db,
                     minimal_patron_only_record, minimal_patron_type_record):
    """Test save patron"""

    # Convenient references
    datastore = LocalProxy(lambda: app.extensions['security'].datastore)
    datastore.create_role(name='patrons')

    PatronType.create(minimal_patron_type_record, dbcommit=True, reindex=True)

    email = 'test_patron@rero.ch'
    u1 = datastore.create_user(
        email=email,
        active=False,
        password=hash_password('aafaf4as5fa')
    )
    datastore.commit()
    u2 = datastore.find_user(email=email)
    assert u1 == u2
    assert 1 == User.query.filter_by(email=email).count()
    email = minimal_patron_only_record.get('email')
    assert datastore.get_user(email) is None

    save_patron(
        minimal_patron_only_record,
        'ptrn',
        Patron,
        None
    )
    email = minimal_patron_only_record.get('email')

    # Verify that user exists in app's datastore
    user_ds = datastore.get_user(email)
    assert user_ds
    assert user_ds.email == email
