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

"""Operation Logs JSONResolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError

from rero_ils.modules.operation_logs.api import OperationLog


def test_operation_log_jsonresolver(item_lib_martigny):
    """Test operation logs json resolver."""
    oplg = OperationLog.get_record_by_pid('1')
    rec = Record.create({
        'operation_log': {'$ref': 'https://ils.rero.ch/api/operation_logs/1'}
    })
    assert rec.replace_refs().get('operation_log') == \
        {'pid': '1', 'type': 'oplg'}

    # deleted record
    oplg.delete()
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()

    # non existing record
    rec = Record.create({
        'operation_logs': {'$ref': 'https://ils.rero.ch/api/operation_logs/n_e'}
    })
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()
