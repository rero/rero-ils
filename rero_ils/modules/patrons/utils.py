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

"""Utilities functions for rero-ils."""


from flask import current_app, url_for
from flask_login import current_user
from flask_security.confirmable import confirm_user
from flask_security.recoverable import send_reset_password_instructions
from invenio_accounts.ext import hash_password
from invenio_indexer.api import RecordIndexer
from werkzeug.local import LocalProxy

from ..utils import clean_dict_keys
from .api import Patron

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def save_patron(data, record_type, record_class, parent_pid):
    """Save a record into the db and index it.

    If the user does not exists, it well be created
    and attached to the patron.
    """
    email = data.get('email')
    data = clean_dict_keys(data)
    data = clean_patron_fields(data)
    # TODO: add the else case
    if email:
        find_user = datastore.find_user(email=email)
        if find_user is None:
            password = hash_password(email)

            datastore.create_user(email=email, password=password)
            datastore.commit()
            # send password reset
            user = datastore.find_user(email=email)
            if user:
                send_reset_password_instructions(user)
                confirm_user(user)

        patron = record_class.get_patron_by_email(email)
        data['is_patron'] = data.get('is_patron', False)
        data['is_patron'] = data.get('is_patron', False)
        if patron:
            patron.update(data, dbcommit=True, reindex=False)
            patron = record_class.get_patron_by_email(email)
        else:
            patron = record_class.create(data, dbcommit=True, reindex=False)

        if patron.get('is_patron', False):
            patron.add_role('patrons')
        else:
            patron.remove_role('patrons')

        if patron.get('is_patron', False):
            patron.add_role('staff')
            # TODO: librarian role
            patron.add_role('librarian')
        else:
            patron.remove_role('librarian')
            # TODO: librarian role
            patron.remove_role('staff')
        patron.dbcommit(reindex=True)
        RecordIndexer().client.indices.flush()

        _next = url_for('invenio_records_ui.ptrn', pid_value=patron.pid)
        return _next, patron.pid


def clean_patron_fields(data):
    """Clean patron fields.

    Remove empty fields and
    validate user fields based on user type (patron/staff).
    """
    for key, value in list(data.items()):
        if not value or value == '':
            del data[key]

    if not data.get('is_patron'):
        if 'barcode' in data:
            del (data['barcode'])
        if 'patron_type_pid' in data:
            del (data['patron_type_pid'])
    if not data.get('is_patron', False):
        if 'library_pid' in data:
            del (data['library_pid'])
    return data


def user_has_patron(user=current_user):
    """Test if user has a patron."""
    try:
        patron = Patron.get_patron_by_email(email=user.email)
        if patron and patron.has_role('patrons'):
            return True
    except Exception:
        pass
    return False
