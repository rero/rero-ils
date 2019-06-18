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

"""Permissions for this module."""


from flask import abort, request
from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.permissions import DynamicPermission
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory

from .modules.patrons.api import Patron

request_item_permission = DynamicPermission(RoleNeed('patron'))
librarian_permission = DynamicPermission(RoleNeed('librarian'))


def user_is_authenticated(user=None):
    """Checks if user is authenticated.

    returns True if user is logged in and authenticated.
    returns False if user is not logged or not authenticated.
    """
    if not user:
        user = current_user
    if user.is_authenticated:
        return True
    return False


def staffer_is_authenticated(user=None):
    """Checks if user (librarian or system_librarian) is authenticated.

    returns patron records if user is logged in and authenticated and has
    librarian or system_librarian role.
    returns False otherwise.
    """
    if not user:
        user = current_user
    if user.is_authenticated:
        patron = Patron.get_patron_by_user(current_user)
        if patron:
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
    returns False if a librarian tries to delete a system_librarian.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron:
            if patron.organisation_pid == record.organisation_pid:
                if patron.is_librarian:
                    if 'system_librarian' in record.get('roles', []):
                        return False
                    return True
                if patron.is_system_librarian:
                    return True
        return False
    return type('Check', (), {'can': can})()


def can_update_organisation_records_factory(record, *args, **kwargs):
    """Checks if the logged user can update records of its organisation.

    user must have librarian or system_librarian role.
    returns False if a librarian tries to update a system_librarian.
    returns False if a librarian tries to add the system_librarian role.
    """
    incoming_record = request.get_json()

    def can(self):
        patron = staffer_is_authenticated()
        if patron:
            if patron.organisation_pid == record.organisation_pid:
                if not patron.is_system_librarian:
                    if (
                        'system_librarian' in incoming_record.get(
                            'roles', []) or
                        'system_librarian' in record.get('roles', [])
                    ):
                        return False
                return True
        return False
    return type('Check', (), {'can': can})()


def can_create_organisation_records_factory(record, *args, **kwargs):
    """Checks if the logged user can create records of its organisation.

    user must have librarian or system_librarian role.
    returns False if a librarian tries to create a system_librarian.
    """
    def can(self):
        if user_is_authenticated():
            if not record:
                return True
            patron = staffer_is_authenticated()
            if patron:
                if patron.organisation_pid == record.organisation_pid:
                    if patron.is_librarian:
                        if 'system_librarian' in record.get('roles', []):
                            return False
                        return True
                    if patron.is_system_librarian:
                            return True
        return False
    return type('Check', (), {'can': can})()


def can_access_organisation_patrons_factory(record, *args, **kwargs):
    """Logged user permissions to access patron records."""
    def can(self):
        if user_is_authenticated():
            patron = Patron.get_patron_by_user(current_user)
            if patron:
                if patron.is_librarian or patron.is_system_librarian:
                    if record:
                        if patron.organisation_pid == record.organisation_pid:
                            return True
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
                if patron:
                    if patron.organisation_pid == item.organisation_pid:
                        return librarian_permission.can()
    return False


def can_edit(user=None):
    """User has editor role."""
    return user_is_authenticated() and librarian_permission.can()


def librarian_permission_factory(record, *args, **kwargs):
    """User has editor role."""
    return librarian_permission


def librarian_delete_permission_factory(record, *args, **kwargs):
    """User can delete record."""
    if record.can_delete:
        return librarian_permission
    abort(403)


def admin_permission_factory(admin_view):
    """Admin permission factory."""
    class FreeAccess(object):
        def can(self):
            return True
    # TODO: remove this bad hacks!
    if admin_view.name in [
        'Circulation',
        'Circulation Settings',
        'Libraries',
        'Items',
        'My Library'] \
       or admin_view.category in [
            'Catalogue',
            'User Services',
            'Admin & Monitoring']:
        return FreeAccess()
    return default_admin_permission_factory(admin_view)


def login_and_librarian():
    """Librarian is logged in."""
    if not current_user.is_authenticated:
        abort(401)
    if not librarian_permission.can():
        abort(403)
