# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Permissions for this module."""

from functools import wraps

from flask import abort, current_app, redirect, request, url_for
from flask_login import current_user
from flask_principal import RoleNeed
from flask_security import login_required, roles_required
from invenio_access.permissions import Permission

from rero_ils.modules.users.models import UserRole

from .modules.patrons.api import current_librarian, current_patrons

request_item_permission = Permission(RoleNeed(UserRole.PATRON))
librarian_permission = Permission(
    RoleNeed(UserRole.PROFESSIONAL_READ_ONLY),
    RoleNeed(UserRole.CATALOG_MANAGER),
    RoleNeed(UserRole.CIRCULATION_MANAGER),
    RoleNeed(UserRole.USER_MANAGER),
    RoleNeed(UserRole.STATISTICS_MANAGER),
    RoleNeed(UserRole.LIBRARY_ADMINISTRATOR),
    RoleNeed(UserRole.ACQUISITION_MANAGER),
    RoleNeed(UserRole.FULL_PERMISSIONS)
)
admin_permission = Permission(RoleNeed('admin'))
editor_permission = Permission(RoleNeed('editor'), RoleNeed('admin'))
monitoring_permission = Permission(RoleNeed('monitoring'))


def admin_permission_factory(record, *args, **kwargs):
    """User has admin role."""
    return admin_permission


def librarian_permission_factory(record, *args, **kwargs):
    """User has librarian role."""
    return librarian_permission


def librarian_update_permission_factory(record, *args, **kwargs):
    """User has editor role and the record is editable."""
    if record.can_edit:
        return librarian_permission
    return type('Check', (), {'can': lambda x: False})()


def librarian_delete_permission_factory(
        record, credentials_only=False, *args, **kwargs):
    """User can delete record."""
    if credentials_only or record.can_delete[0]:
        return librarian_permission
    return type('Check', (), {'can': lambda x: False})()


def login_and_librarian():
    """Librarian is logged in."""
    if not current_user.is_authenticated:
        abort(401)
    if not librarian_permission.can():
        abort(403)


def login_and_patron():
    """Patron is logged in.

    :return a tuple with 3 values:
      * bool: check if the user is connected and has a patron role.
      * int: the http return code (200, 401, 403).
      * string: the redirect url to use (optional).
    """
    if current_user and not current_user.is_authenticated:
        redirect_url = url_for('security.login', next=request.path)
        return False, 401, redirect_url
    if len(current_patrons) == 0:
        return False, 403, None
    return True, 200, None


def can_access_professional_view(func):
    """Check if user is librarian or system librarian.

    and give access to professional view.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_librarian:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


def check_user_is_authenticated(redirect_to=None, code=302):
    """Check if user is authenticated.

    If user isn't authenticated :
      - either it is redirected to a page if 'redirect_to' is defined.
      - either request is aborted (HTTP 403).
    :param redirect_to: the URL to redirect the user if it's not authenticated.
    :param code: the HTTP code to use for redirect (default=302)
    """
    def inner_function(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if current_user.is_authenticated:
                return func(*args, **kwargs)
            elif redirect_to:
                return redirect(url_for(redirect_to), code)
            else:
                abort(403)
        return decorated_view
    return inner_function


def wiki_edit_view_permission():
    """Wiki edition permission.

    :return: true if the logged user has the editor role
    """
    @login_required
    @roles_required('editor')
    def foo():
        return True
    return foo()


def wiki_edit_ui_permission():
    """Wiki edition permision for the user interface.

    Mainly used to display buttons in the user interface.
    :return: true if the logged user has the editor role
    """
    return editor_permission.can()


def can_receive_regular_issue(holding):
    """Checks if logged user can receive a regular issue of its organisation.

    user must have librarian or system_librarian role.
    returns False if a librarian tries to receive anissue of another library.
    """
    if not current_librarian:
        return False
    if current_librarian.organisation_pid == holding.organisation_pid:
        if current_librarian.has_full_permissions:
            return True
        if holding.library_pid not in current_librarian.library_pids:
            return False
        return True
    return False
