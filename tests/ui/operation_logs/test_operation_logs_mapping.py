# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Operation logs search index mapping tests."""

from rero_ils.modules.operation_logs.api import OperationLog
from tests.utils import get_mapping


def test_operation_log_search_mapping(item_lib_sion, operation_log_data):
    """Test operation log search index mapping."""
    mapping = get_mapping(OperationLog.index_name)
    assert mapping
    OperationLog.create(operation_log_data)
    assert mapping == get_mapping(OperationLog.index_name)
