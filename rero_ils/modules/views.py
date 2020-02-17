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

"""Blueprint used for loading templates for all modules."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, jsonify
from flask_login import current_user

from .permissions import record_update_delete_permissions
from ..permissions import librarian_permission

api_blueprint = Blueprint(
    'api_blueprint',
    __name__,
    url_prefix=''
)


def check_authentication(func):
    """Decorator to check authentication for permissions HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not librarian_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)

    return decorated_view


@api_blueprint.route(
    '/permissions/<route_name>/<record_pid>', methods=['GET'])
@check_authentication
def permissions(route_name, record_pid):
    """HTTP GET request for record permissions.

    Required parameters: route_name, record_pid
    """
    return record_update_delete_permissions(
        record_pid=record_pid, route_name=route_name)
