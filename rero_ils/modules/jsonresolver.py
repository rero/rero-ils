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
from invenio_pidstore.models import PersistentIdentifier


def resolve_json_refs(pid_type, pid):
    """Resolver for $ref in record.

    :param pid_type: type of pid
    :param pid: pid to resolve
    :return: resolved persistent identifier
    """
    try:
        persistent_id = PersistentIdentifier.get(pid_type, pid)
    except Exception as error:
        current_app.logger.error(f"Unable to resolve {pid_type} pid: {pid}")
        raise error

    if persistent_id.is_redirected():
        persistent_id = persistent_id.get_redirect()
    return {"pid": persistent_id.pid_value, "type": pid_type}
