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

"""Permissions for all modules."""


from flask import jsonify

from .utils import get_record_class_update_permission_from_route


def jsonify_permission_api_response(
        can_update=False, can_delete=False, reasons={}):
    """Jsonify api response."""
    return jsonify({
        'update': {'can': can_update},
        'delete': {'can': can_delete, 'reasons': reasons}
    })


def record_update_delete_permissions(record_pid=None, route_name=None):
    """Return record permissions."""
    try:
        rec_class, update_permission = \
            get_record_class_update_permission_from_route(route_name)
        record = rec_class.get_record_by_pid(record_pid)

        if not record:
            return jsonify({'status': 'error: Record not found.'}), 404

        return jsonify_permission_api_response(
            can_update=update_permission(record).can(),
            can_delete=record.can_delete,
            reasons=record.reasons_not_to_delete(),
        )
    except Exception as error:
        return jsonify({'status': 'error: Bad request'}), 400
