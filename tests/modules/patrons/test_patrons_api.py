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
from werkzeug.local import LocalProxy

from reroils_app.modules.documents_items.api import DocumentsWithItems
from reroils_app.modules.patrons.api import Patron
from reroils_app.modules.patrons.utils import save_patron


@mock.patch('reroils_app.modules.patrons.utils.confirm_user')
@mock.patch(
    'reroils_app.modules.patrons.utils.send_reset_password_instructions'
)
@mock.patch('reroils_app.modules.patrons.utils.url_for')
@mock.patch('reroils_record_editor.utils.url_for')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.patrons.api.Patron._get_uuid_pid_by_email')
@mock.patch(
    'reroils_app.modules.patrons.api.Patron.get_borrowed_documents_pids'
)
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
def test_patron(reindex, get_borrowed_documents_pids, get_uuid_pid_by_email,
                record_indexer, url_for1, url_for2, send_email, confirm_user,
                app, db, minimal_patron_record, minimal_document_record,
                minimal_item_record):
    """Test patron"""

    # Convenient references
    security = LocalProxy(lambda: app.extensions['security'])
    datastore = LocalProxy(lambda: security.datastore)
    # hack the return value
    get_uuid_pid_by_email.return_value = None, None

    next, pid = save_patron(
        minimal_patron_record,
        Patron.provider.pid_type,
        Patron.fetcher,
        Patron.minter,
        record_indexer,
        Patron,
        None
    )
    email = minimal_patron_record.get('email')

    # Verify that user exists in app's datastore
    user = datastore.get_user(email)
    assert user

    # hack the return value
    get_uuid_pid_by_email.return_value = pid.object_uuid, pid.id
    patron = Patron.get_patron_by_email(email)
    assert patron.get('email') == email

    patron = Patron.get_patron_by_user(user)
    assert patron.get('email') == email

    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)

    # hack the return value
    get_borrowed_documents_pids.return_value = [doc.pid]
    docs = patron.get_borrowed_documents()
    assert docs[0] == doc
