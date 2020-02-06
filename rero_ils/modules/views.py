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

"""Blueprint for all modules."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, abort
from flask import request as flask_request
from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.permissions import DynamicPermission

from .patrons.api import Patron
from .permissions import record_permissions

librarian_permission = DynamicPermission(RoleNeed('librarian'))

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)


def login_and_librarian():
    """Librarian is logged in."""
    if not current_user.is_authenticated:
        abort(401)
    if not librarian_permission.can():
        abort(403)


def check_permission(fn):
    """Check user permissions."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        """Decorated view."""
        login_and_librarian()
        return fn(*args, **kwargs)
    return decorated_view


@api_blueprint.route(
    '/permissions/<record_type>/<record_pid>', methods=['GET'])
@check_permission
def permissions(record_pid, record_type):
    """HTTP GET request for record permissions.

    Required parameters: record_pid, record_type
    Optional parameters: user_pid, it is the logged user pid if not given
    """
    if record_type != 'documents':
        abort(401)
    user_pid = flask_request.args.get('user_pid')
    if not user_pid:
        user_pid = Patron.get_patron_by_user(current_user).pid
    return record_permissions(record_pid, user_pid)
