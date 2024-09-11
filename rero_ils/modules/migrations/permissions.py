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

"""Permissions for migrations."""
from functools import wraps

from elasticsearch_dsl import Q
from flask import abort, jsonify, make_response
from flask_login import current_user
from invenio_access import action_factory

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)


def check_permission(permission):
    """Decorator to check if current connected user has access to an action.

    :param actions: List of `ActionNeed` to test. If one permission failed
        then the access should be unauthorized.
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(make_response(jsonify({"status": "error: Unauthorized"}), 401))
            if not permission.can():
                abort(make_response(jsonify({"status": "error: Forbidden"}), 403))
            return func(*args, **kwargs)

        return wrapper

    return inner


# Actions to control library policy
search_action = action_factory("mig-search")
read_action = action_factory("mig-read")
access_action = action_factory("mig-access")


class MigrationPermissionPolicy(RecordPermissionPolicy):
    """Library Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]

    @property
    def query_filters(self):
        """List of search engine query filters.

        These filters consist of additive queries mapping to what the current
        user should be able to retrieve via search.
        """
        if current_librarian:
            return Q("term", organisation_pid=current_librarian.organisation_pid)
        return Q("match_none")
