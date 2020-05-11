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

from .utils import get_record_class_permissions_factories_from_route


def record_permissions(record_pid=None, route_name=None):
    """Return record permissions."""
    try:
        rec_class, create_permission, update_permission, delete_permission = \
            get_record_class_permissions_factories_from_route(route_name)

        # To check create permission, we don't need to check if the record_pid
        # exists. Just call the create permission (if exists) with `None` value
        # as record.
        permissions = {
            'create': {'can': True}
        }
        if create_permission:
            permissions['create']['can'] = create_permission(record=None).can()

        # If record_pid is not None, we can check about 'delete' and 'update'
        # permissions.
        if record_pid:
            record = rec_class.get_record_by_pid(record_pid)
            if not record:
                return jsonify({'status': 'error: Record not found.'}), 404

            # To check if the record could be update, just call the update
            # permission factory to get the answer
            permissions['update'] = {'can': update_permission(record).can()}

            # We have two behaviors for 'can_delete'. Either the record has
            # linked resources and so children resources should be deleted
            # before ; either the `delete_permissions_factory` for this record
            # should be called. If this call send 'False' then the
            # reason_not_to_delete should be "permission denied"
            permissions['delete'] = {
                'can': record.can_delete and delete_permission(record).can()
            }
            reasons = record.reasons_not_to_delete()
            if not permissions['delete']['can'] and not reasons:
                # in this case, it's because config delete factory return
                # `False`, so the reason is 'Permission denied'
                reasons = {'others': {'permission': 'permission denied'}}
            permissions['delete']['reasons'] = reasons

        return jsonify(permissions)
    except Exception:
        return jsonify({'status': 'error: Bad request'}), 400
