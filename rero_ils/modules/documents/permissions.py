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

"""Document permissions."""

from flask import jsonify
from flask_login import current_user

from .api import Document
from ..patrons.api import Patron


def document_update_permission_factory():
    """User has librarian role."""
    for role in current_user.roles:
        if role.name == 'librarian':
            return type('Check', (), {'can': lambda x: True})()
    return type('Check', (), {'can': lambda x: False})()


def jsonify_response(can_update=False, can_delete=False, reasons={}):
    """Jsonify api response."""
    return jsonify({
        'update': {'can': document_update_permission_factory().can()},
        'delete': {'can': can_delete, 'reasons': reasons}
    })


def document_permissions(document_pid, user_pid):
    """Return document permissions."""
    document = Document.get_record_by_pid(document_pid)
    if not document:
        return jsonify_response(reasons='Document not found.')
    user = Patron.get_record_by_pid(user_pid)
    if not user:
        return jsonify_response(reasons='User not found.')
    if document.can_delete:
        return jsonify_response(can_delete=True)
    else:
        return jsonify_response(reasons=document.reasons_not_to_delete())
