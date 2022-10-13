# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

from elasticsearch_dsl.query import Q
from flask import abort
from flask_login import current_user

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import RecordPermission, \
    record_permission_factory
from rero_ils.modules.stats_cfg.api import StatsCfgSearch
from rero_ils.permissions import admin_permission, librarian_permission, \
    monitoring_permission


class StatPermission(RecordPermission):
    """Stat permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # Operation allowed only for admin, librarian and
        # system librarian members
        return admin_permission.require().can() \
            or monitoring_permission.require().can() \
            or librarian_permission.require().can()

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # Case librarian: filter data by libraries of librarian and
        # deny access to 'billing' statistics
        if not (admin_permission.require().can() or
                monitoring_permission.require().can()):
            if librarian_permission.require().can():
                if 'type' not in record or record['type'] == 'billing':
                    return False
                elif record['type'] == 'librarian':
                    record = filter_stat_by_librarian(record)
                else:
                    if not current_librarian.is_system_librarian:
                        return False
                    org_pid = current_librarian.organisation_pid
                    if record['values']:
                        if not record['values'][0]['org_pid'] == org_pid:
                            return False

        return admin_permission.require().can() \
            or monitoring_permission.require().can() \
            or librarian_permission.require().can()

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        return False

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        return False

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        return False


def stats_ui_permission_factory(record, *args, **kwargs):
    """Permission for stats detailed view."""
    return record_permission_factory(
            action='read', record=record, cls=StatPermission)


def filter_stat_by_librarian(record):
    """Filter data for libraries of specific librarian/system_librarian.

    :param record: statistics to check.
    :return: statistics filtered by libraries.
    """
    from rero_ils.modules.stats.api import StatsForLibrarian

    library_pids = StatsForLibrarian.get_librarian_library_pids()
    record['values'] = list(filter(lambda lib: lib['library']['pid'] in
                            library_pids, record['values']))
    return record


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
        if not librarian_permission.require().can():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def permission_filter():
    """Permission filter.

    Display only stats reports for the current system librarian organisation
    or stats type librarian.
    """
    if current_librarian:
        if current_librarian.is_system_librarian:
            org_pid = current_librarian.organisation_pid
            search = StatsCfgSearch()\
                .filter('term', org_pid=org_pid)\
                .source(['pid'])\
                .scan()
            config_pids = [s['pid'] for s in search]
            return [Q('terms', config_pid=config_pids)
                    | Q('term', type='librarian')]
        else:
            return [Q('term', type='librarian')]

    return None
