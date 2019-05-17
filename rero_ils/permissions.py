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


from flask import abort
from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.permissions import DynamicPermission
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory

from .modules.patrons.api import Patron

request_item_permission = DynamicPermission(RoleNeed('patron'))


def login_and_librarian():
    """Librarian is logged in."""
    if not current_user.is_authenticated:
        abort(401)
    if not librarian_permission.can():
        abort(403)


librarian_permission = DynamicPermission(RoleNeed('librarian'))


def can_access_item(user=None, item=None):
    """User has librarian role and logged in and in same item organisation."""
    if not user:
        user = current_user
    if item:
        patron = Patron.get_patron_by_user(user)
        if patron.organisation_pid == item.organisation_pid:
            return user.is_authenticated and librarian_permission.can()
    return False


def can_edit(user=None):
    """User has editor role."""
    if not user:
        user = current_user
    return user.is_authenticated and librarian_permission.can()


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


def organisation_access_factory(record, *args, **kwargs):
    """User access only records of its organisation."""
    def can(self):
        if current_user.is_authenticated:
            patron = Patron.get_patron_by_user(current_user)
            if (
                    patron and 'librarian' in patron.get('roles') and
                    patron.organisation_pid == record.organisation_pid
            ):
                    return True
            return False
    return type('Check', (), {'can': can})()


def organisation_create_factory(record, *args, **kwargs):
    """User create only records of its organisation."""
    from flask import current_app

    def can(self):
        if current_user.is_authenticated:
            if not record:
                return True
            patron = Patron.get_patron_by_user(current_user)
            if (
                    patron and 'librarian' in patron.get('roles') and
                    patron.organisation_pid == record.organisation_pid
            ):
                    return True
            return False
    return type('Check', (), {'can': can})()
