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

"""Permissions for this module."""

from functools import wraps

from flask import abort, current_app
from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.permissions import Permission
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory

from .modules.patrons.api import Patron

request_item_permission = Permission(RoleNeed('patron'))
librarian_permission = Permission(RoleNeed('librarian'))


def user_is_authenticated(user=None):
    """Checks if user is authenticated.

    :returns: True if user is logged in and authenticated.
    :returns False if user is not logged or not authenticated.
    """
    if not user:
        user = current_user
    if user.is_authenticated:
        return True
    return False


def staffer_is_authenticated(user=None):
    """Checks if user (librarian or system_librarian) is authenticated.

    :returns: patron records if user is logged in and authenticated and has
    librarian or system_librarian role.
    :returns False otherwise.
    """
    if not user:
        user = current_user
    if user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron and (patron.is_librarian or patron.is_system_librarian):
            return patron
    return None


def patron_is_authenticated(user=None):
    """Checks if user (with role patron) is authenticated.

    :returns: Patron records if user is logged in and authenticated and has
    the patron role.
    :returns False otherwise.
    """
    if not user:
        user = current_user
    if user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron and patron.is_patron:
            return patron
    return None


def can_access_organisation_records_factory(record, *args, **kwargs):
    """Checks if the logged user have access to records of its organisation.

    user must have librarian or system_librarian role.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if patron.is_librarian or patron.is_system_librarian:
                return True
        return False
    return type('Check', (), {'can': can})()


def can_delete_organisation_records_factory(record, *args, **kwargs):
    """Checks if the logged user can delete records of its organisation.

    user must have librarian or system_librarian role.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            return True
        return False
    return type('Check', (), {'can': can})()


def can_update_organisation_records_factory(record, *args, **kwargs):
    """Checks if the logged user can update records of its organisation.

    user must have librarian or system_librarian role.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            return True
        return False
    return type('Check', (), {'can': can})()


def can_create_organisation_records_factory(record, *args, **kwargs):
    """Checks if the logged user can create records of its organisation.

    user must have librarian or system_librarian role.
    returns False if a librarian tries to create a system_librarian.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and not record:
            return True
        if patron and patron.organisation_pid == record.organisation_pid:
            if patron.is_system_librarian:
                return True
            if patron.is_librarian:
                if 'system_librarian' in record.get('roles', []):
                    return False
                if patron.library_pid and \
                        isinstance(record, Patron) and \
                        record.library_pid and \
                        record.library_pid != patron.library_pid:
                    return False
                return True
        return False
    return type('Check', (), {'can': can})()


def can_access_organisation_patrons_factory(record, *args, **kwargs):
    """Logged user permissions to access patron records."""
    def can(self):
        patron = staffer_is_authenticated()
        if patron:
            return True
        return False
    return type('Check', (), {'can': can})()


def can_access_item(user=None, item=None):
    """Checks if user has the librarian role.

    and is in the same organisation as the given item.
    """
    if item:
        if not user:
            user = current_user
        if user.is_authenticated:
            patron = Patron.get_patron_by_user(user)
            if patron and patron.organisation_pid == item.organisation_pid:
                return librarian_permission.can()
    return False


def can_edit(user=None):
    """User has editor role."""
    return user_is_authenticated() and librarian_permission.can()


def librarian_permission_factory(record, *args, **kwargs):
    """User has editor role."""
    return librarian_permission


def librarian_update_permission_factory(record, *args, **kwargs):
    """User has editor role and the record is editable."""
    if record.can_edit:
        return librarian_permission
    return type('Check', (), {'can': lambda x: False})()


def librarian_delete_permission_factory(
        record, credentials_only=False, *args, **kwargs):
    """User can delete record."""
    if credentials_only:
        return librarian_permission
    if record.can_delete:
        return librarian_permission
    return type('Check', (), {'can': lambda x: False})()


def login_and_librarian():
    """Librarian is logged in."""
    if not current_user.is_authenticated:
        abort(401)
    if not librarian_permission.can():
        abort(403)


def can_access_professional_view(func):
    """Check if user is librarian or system librarian.

    and give access to professional view.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        else:
            patron = Patron.get_patron_by_user(current_user)
            if patron.is_librarian or patron.is_system_librarian:
                return func(*args, **kwargs)
            else:
                abort(403)
    return decorated_view


def can_read_update_delete_acquisition_factory(record, *args, **kwargs):
    """Checks if logged user can update or delete its org acquisition resources.

    user must have librarian or system_librarian role
    librarian can only update or delete its affiliated library acquisition
    resources.
    sys_librarian can update or delete any acquisition resource of its org.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if not patron.is_system_librarian:
                if patron.library_pid and \
                        record.library_pid != patron.library_pid:
                    return False
            return True
        return False
    return type('Check', (), {'can': can})()


def can_create_acquisition_factory(record, *args, **kwargs):
    """Checks if the logged user can create acquisition resource of its org.

    librarian can create acquisition resource for its library only.
    system_librarian can create acquisition resource at any library of its org.
    system_librarian or librarian can not create acquisition resource at
    another org.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and not record:
            return True
        if patron and patron.organisation_pid == record.organisation_pid:
            if patron.is_system_librarian:
                return True
            if patron.is_librarian and \
                    record.library_pid == patron.library_pid:
                return True
        return False
    return type('Check', (), {'can': can})()


def can_list_acquisition_factory(record, *args, **kwargs):
    """Checks if the logged user have access to list acquisition resources.

    only authenticated users can place a search on acquisition resources.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron:
            return True
        return False
    return type('Check', (), {'can': can})()
