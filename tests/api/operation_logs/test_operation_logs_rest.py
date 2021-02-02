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

"""Tests REST API operation logs."""

import mock
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.operation_logs.api import OperationLogsSearch
from rero_ils.modules.operation_logs.models import OperationLogOperation


def test_operation_log_entries(
    client, librarian_martigny, document):
    """Test operation log entries after record update."""
    with mock.patch(
        'rero_ils.modules.operation_logs.listener.current_patron',
        librarian_martigny
    ):
        login_user_via_session(client, librarian_martigny.user)
        print('_start_here')
        document.update(
            document, dbcommit=True, reindex=True)
    search = OperationLogsSearch()
    results = search.filter('term',
        operation=OperationLogOperation.UPDATE).filter(
        'term', record__pid=document.pid).filter(
        'term', user_name=librarian_martigny.formatted_name
    ).source().count()

    assert results == 1
