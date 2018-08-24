# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Utils tests."""

from __future__ import absolute_import, print_function

import mock
from flask_security.utils import hash_password
from invenio_accounts.models import User
from werkzeug.local import LocalProxy

from reroils_app.modules.patrons.api import Patron
from reroils_app.modules.patrons.utils import save_patron, structure_document


@mock.patch('reroils_app.modules.patrons.utils.confirm_user')
@mock.patch(
    'reroils_app.modules.patrons.utils.send_reset_password_instructions'
)
@mock.patch('reroils_app.modules.patrons.utils.url_for')
@mock.patch('reroils_record_editor.utils.url_for')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
@mock.patch('reroils_app.modules.patrons.api.Patron._get_uuid_pid_by_email')
def test_save_patron(get_uuid_pid_by_email, reindex, record_indexer, url_for1,
                     url_for2, send_email, confirm_user, app, db,
                     minimal_patron_only_record):
    """Test save patron"""

    # Convenient references
    security = LocalProxy(lambda: app.extensions['security'])
    datastore = LocalProxy(lambda: security.datastore)
    datastore.create_role(name='patrons')

    # hack the return value
    get_uuid_pid_by_email.return_value = None, None

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
        Patron.provider.pid_type,
        Patron.fetcher,
        Patron.minter,
        record_indexer,
        Patron,
        None
    )
    email = minimal_patron_only_record.get('email')

    # Verify that user exists in app's datastore
    user_ds = datastore.get_user(email)
    assert user_ds
    assert user_ds.email == email


def test_structure_document(minimal_item_record):
    """Test structure document"""
    class Doc:
        def dumps(self):
            return {
                'itemslist': [
                    minimal_item_record
                ]
            }

    docs = [Doc()]
    loans, pendings = structure_document(docs, '123456')

    assert len(loans) == 1
    assert len(pendings) == 0
