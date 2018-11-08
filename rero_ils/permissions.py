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


from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.permissions import DynamicPermission
from invenio_admin.permissions import \
    admin_permission_factory as default_admin_permission_factory

request_item_permission = DynamicPermission(RoleNeed('patrons'))


def can_request(user=None):
    """User can request items."""
    if not user:
        user = current_user
    return user.is_authenticated and request_item_permission.can()


record_edit_permission = DynamicPermission(RoleNeed('cataloguer'))


def can_edit(user=None):
    """User has editor role."""
    if not user:
        user = current_user
    return user.is_authenticated and record_edit_permission.can()


def cataloguer_permission_factory(record, *args, **kwargs):
    """User has editor role."""
    return record_edit_permission


def admin_permission_factory(admin_view):
    """."""
    class FreeAccess(object):
        def can(self):
            return True
    # TODO: remove this bad hacks!
    if admin_view.name in [
        'Circulation',
        'Circulation Settings',
        'Libraries',
        'My Library'] \
       or admin_view.category in ['Resources']:
        return FreeAccess()
    return default_admin_permission_factory(admin_view)
