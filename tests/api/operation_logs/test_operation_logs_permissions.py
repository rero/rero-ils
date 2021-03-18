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

from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.operation_logs.permissions import OperationLogPermission
from rero_ils.modules.utils import get_ref_for_pid


def test_operation_logs_permissions_api(
        client, document, patron_sion,
        librarian_martigny):
    """Test operation log permissions api."""
    oplg = OperationLog.get_record_by_pid('1')

    operation_log_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='operation_logs'
    )
    operation_log_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='operation_logs',
        record_pid=oplg.pid
    )

    # Not logged
    res = client.get(operation_log_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_sion.user)
    res = client.get(operation_log_permissions_url)
    assert res.status_code == 403

    # Logged as
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(operation_log_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['create']['can']
    assert not data['delete']['can']
    assert data['list']['can']
    assert data['read']['can']
    assert not data['update']['can']


def test_operation_logs_permissions(patron_martigny, org_martigny,
                                    librarian_martigny, org_sion,
                                    item_lib_martigny,
                                    system_librarian_martigny):
    """Test operation log permissions class."""

    oplg = OperationLog.get_record_by_pid('1')

    # Anonymous user
    assert not OperationLogPermission.list(None, {})
    assert not OperationLogPermission.read(None, {})
    assert not OperationLogPermission.create(None, {})
    assert not OperationLogPermission.update(None, {})
    assert not OperationLogPermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.operation_logs.permissions.current_patron',
        patron_martigny
    ):
        assert not OperationLogPermission.list(None, oplg)
        assert not OperationLogPermission.read(None, oplg)
        assert not OperationLogPermission.create(None, oplg)
        assert not OperationLogPermission.update(None, oplg)
        assert not OperationLogPermission.delete(None, oplg)

    oplg_sion = deepcopy(oplg)
    oplg_sion['organisation'] = {'$ref': get_ref_for_pid('org', org_sion.pid)}
    oplg_sion = OperationLog.create(
        oplg, dbcommit=True, reindex=True, delete_pid=True)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.operation_logs.permissions.current_patron',
        librarian_martigny
    ):
        assert OperationLogPermission.list(None, oplg)
        assert OperationLogPermission.read(None, oplg)
        assert not OperationLogPermission.create(None, oplg)
        assert not OperationLogPermission.update(None, oplg)
        assert not OperationLogPermission.delete(None, oplg)

        assert OperationLogPermission.read(None, oplg)
        assert not OperationLogPermission.create(None, oplg)
        assert not OperationLogPermission.update(None, oplg)
        assert not OperationLogPermission.delete(None, oplg)

        assert OperationLogPermission.read(None, oplg_sion)
        assert not OperationLogPermission.create(None, oplg_sion)
        assert not OperationLogPermission.update(None, oplg_sion)
        assert not OperationLogPermission.delete(None, oplg_sion)

    # # As System-librarian
    # with mock.patch(
    #     'rero_ils.modules.operation_logs.permissions.current_patron',
    #     system_librarian_martigny
    # ):
    #     assert not OperationLogPermission.list(None, oplg)
    #     assert not OperationLogPermission.read(None, oplg)
    #     assert not OperationLogPermission.create(None, oplg)
    #     assert not OperationLogPermission.update(None, oplg)
    #     assert not OperationLogPermission.delete(None, oplg)

    #     assert not OperationLogPermission.read(None, oplg_sion)
    #     assert not OperationLogPermission.create(None, oplg_sion)
    #     assert not OperationLogPermission.update(None, oplg_sion)
    #     assert not OperationLogPermission.delete(None, oplg_sion)
