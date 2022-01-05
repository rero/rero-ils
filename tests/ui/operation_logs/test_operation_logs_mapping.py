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

from rero_ils.modules.operation_logs.api import OperationLog


def test_operation_log_es_mapping(item_lib_sion, operation_log_data):
    """Test operation log elasticsearch mapping."""
    mapping = get_mapping(OperationLog.index_name)
    assert mapping
    OperationLog.create(operation_log_data)
    assert mapping == get_mapping(OperationLog.index_name)
