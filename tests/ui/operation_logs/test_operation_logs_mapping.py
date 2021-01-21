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

"""Operation logs elasticsearch mapping tests."""

from utils import get_mapping

from rero_ils.modules.operation_logs.api import OperationLog, \
    OperationLogsSearch
from rero_ils.modules.operation_logs.models import OperationLogOperation


def test_operation_log_es_mapping(item_lib_sion, operation_log_1_data):
    """Test operation log elasticsearch mapping."""
    search = OperationLogsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    OperationLog.create(
        operation_log_1_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)

    count = search.query(
        'query_string', query=OperationLogOperation.CREATE
    ).count()
    assert count == 3

    count = search.query(
        'query_string', query=OperationLogOperation.UPDATE
    ).count()
    assert count == 4

    count = search.query(
        'match',
        **{'user_name': 'updated_user'}).\
        count()
    assert count == 1
