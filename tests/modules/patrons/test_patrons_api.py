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

from werkzeug.local import LocalProxy

from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.utils import save_patron


def test_patron(app, db, minimal_patron_record, minimal_document_record,
                limited_item_record):
    """Test patron"""

    # Convenient references
    datastore = LocalProxy(lambda: app.extensions['security'].datastore)
    next, pid = save_patron(
        minimal_patron_record,
        'ptrn',
        Patron,
        None
    )
    email = minimal_patron_record.get('email')

    # Verify that user exists in app's datastore
    user = datastore.get_user(email)
    assert user

    patron = Patron.get_patron_by_email(email)
    assert patron.get('email') == email

    patron = Patron.get_patron_by_user(user)
    assert patron.get('email') == email
