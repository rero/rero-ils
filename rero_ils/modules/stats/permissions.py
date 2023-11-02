# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Permissions for stats."""

from functools import wraps

from flask import abort, g
from flask_login import current_user
from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Disable

from rero_ils.modules.permissions import AllowedByAction, OrganisationNeed, \
    RecordPermissionPolicy
from rero_ils.permissions import admin_permission

from .models import StatType

# Actions to control statistics policies for CRUD operations
search_action = action_factory('stat-search')
read_action = action_factory('stat-read')
access_action = action_factory('stat-access')


class RestrictStatistics(AllowedByAction):
    """Allow if the user and the record have the same organisation."""

    def excludes(self, record=None, **kwargs):
        """Disallow operation check.

        :param record; the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        if (
            record
            and record.get('type') == StatType.BILLING
            and not admin_permission.require().can()
        ):
            return [any_user]
        return []

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action.

        :param record: the record to check.
        :param args: extra arguments.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to validate access.
        """
        if record and record.get('type') == StatType.REPORT:
            # Check if the record organisation match an ``OrganisationNeed``
            required_need = OrganisationNeed(record.organisation_pid)
            if required_need not in g.identity.provides:
                return []
        return super().needs(record, **kwargs)


class StatisticsPermissionPolicy(RecordPermissionPolicy):
    """Statistics permission policy used by the CRUD operations."""

    can_search = [
        AllowedByAction(search_action)
    ]
    can_read = [
        RestrictStatistics(read_action),
        AllowedByAction(search_action)
    ]
    can_create = [Disable()]
    can_update = [Disable()]
    can_delete = [Disable()]


class StatisticsUIPermissionPolicy(RecordPermissionPolicy):
    """Statistics permission policy used by the CRUD operations."""

    can_read = [
        RestrictStatistics(read_action),
        AllowedByAction(read_action)
    ]


def stats_ui_permission_factory(record, *args, **kwargs):
    """Permission for stats detailed view."""
    return StatisticsUIPermissionPolicy('read', record=record)


# DECORATORS ==================================================================
#   Decorators used to protect access to some API blueprints

def check_logged_as_admin(fn):
    """Decorator to check if the current logged user is logged as an admin.

    If no user is connected: return 401 (unauthorized)
    If current logged user has not the `admin` role: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not admin_permission.require().can():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def check_logged_as_librarian(fn):
    """Decorator to check if the current logged user is logged as an librarian.

    If no user is connected: return 401 (unauthorized)
    If current logged user has not the `librarian` role: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not StatisticsUIPermissionPolicy('read').require().can():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper
