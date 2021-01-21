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

"""Operation logs Record tests."""

from __future__ import absolute_import, print_function

from utils import flush_index, get_mapping

from rero_ils.modules.operation_logs.api import OperationLog, \
    OperationLogsSearch
from rero_ils.modules.operation_logs.api import \
    operation_log_id_fetcher as fetcher
from rero_ils.modules.operation_logs.models import OperationLogOperation


def test_operation_logs_es_mapping(db, item_lib_sion, operation_log_1_data):
    """Test operation logs elasticsearch mapping."""
    search = OperationLogsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    oplg = OperationLog.create(operation_log_1_data, dbcommit=True,
                             reindex=True, delete_pid=True)
    flush_index(OperationLogsSearch.Meta.index)
    assert mapping == get_mapping(search.Meta.index)

    assert oplg == operation_log_1_data
    assert oplg.get('pid') == '7'

    oplg = OperationLog.get_record_by_pid('7')
    assert oplg == operation_log_1_data

    fetched_pid = fetcher(oplg.id, oplg)
    assert fetched_pid.pid_value == '7'
    assert fetched_pid.pid_type == 'oplg'
    
    assert oplg.get('operation') == OperationLogOperation.UPDATE
