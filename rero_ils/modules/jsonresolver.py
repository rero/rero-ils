# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""General resolver."""

from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


def resolve_json_refs(pid_type, pid, raise_on_error=True):
    """Resolver for $ref in record.

    :param pid_type: type of pid
    :param pid: pid to resolve
    :return: resolved persistent identifier
    """
    try:
        persistent_id = PersistentIdentifier.get(pid_type, pid)
    except Exception:
        current_app.logger.error(f'Unable to resolve {pid_type} pid: {pid}')
    else:
        if persistent_id.status == PIDStatus.REGISTERED:
            return dict(
                pid=persistent_id.pid_value,
                type=pid_type
            )
        base_item_route = current_app.config.get(
            'RECORDS_REST_ENDPOINTS'
        ).get(pid_type, {}).get('item_route', '/???')
        item_route_parts = ['api'] + base_item_route.split('/')[1:-1] + [pid]
        item_route = '/'.join(item_route_parts)
        msg = f' Resolve {pid_type}: {item_route} {persistent_id}'
        current_app.logger.error(msg)
    if raise_on_error:
        raise Exception(f'Unable to resolve {pid_type} pid: {pid}')
