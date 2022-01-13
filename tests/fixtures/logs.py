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

"""OperationLog pytest fixtures and plugins."""
from copy import deepcopy

import pytest

from rero_ils.modules.operation_logs.api import OperationLog


@pytest.fixture(scope="module")
def circulation_logs_data(operation_logs):
    """Load circulation log data."""
    return deepcopy([
        data
        for pid, data in operation_logs.items()
        if data.get('loan', {}).get('trigger')
    ])


@pytest.fixture(scope="module")
def circulation_logs(app, circulation_logs_data):
    """Load circulation log records."""
    return [
        OperationLog.create(data, index_refresh=True)
        for data in circulation_logs_data
    ]
