# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Persistent identifier minters."""
from collections import namedtuple

EntityMinter = namedtuple(
    'EntityMinter',
    ['pid_type', 'pid_value', 'object_uuid', 'object_type'])


def id_minter(record_uuid, data, provider, pid_key='pid', object_type='rec'):
    """RERO ILS dummy minter."""
    # DEV NOTES:
    # A minter is required for invenio-records-rest.
    # This return a dummy PersistentIdentifier
    return EntityMinter(
        pid_type=object_type,
        pid_value=data['pid'],
        object_uuid=record_uuid,
        object_type=object_type
    )
