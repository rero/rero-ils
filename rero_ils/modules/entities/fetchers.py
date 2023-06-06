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

"""Persistent identifier fetchers."""


from __future__ import absolute_import, print_function

from collections import namedtuple

from rero_ils.modules.utils import get_pid_type_from_schema

FetchedPID = namedtuple('FetchedPID', ['pid_type', 'pid_value'])
"""A pid fetcher."""


def id_fetcher(record_uuid, data):
    """Fetch a record's identifier.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :return: A :data:`rero_ils.modules.fetchers.FetchedPID` instance.
    """
    pid_type = 'ent'
    # try to extract pid type from schema
    if schema := data.get('$schema'):
        pid_type = get_pid_type_from_schema(schema)
    return FetchedPID(
        pid_type=pid_type,
        pid_value=data['pid']
    )
