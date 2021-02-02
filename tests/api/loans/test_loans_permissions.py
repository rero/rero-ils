# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.loans.permissions import LoanPermission


def test_loans_permissions_api(client, patron_martigny,
                               loan_overdue_martigny, loan_overdue_sion,
                               loan_overdue_saxon,
                               system_librarian_martigny):
    """Test loans permissions api."""
    loan_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='loans'
    )
    loan_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='loans',
        record_pid=loan_overdue_martigny.pid
    )
    loan_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='loans',
        record_pid=loan_overdue_saxon.pid
    )
    loan_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='loans',
        record_pid=loan_overdue_sion.pid
    )

    # Not logged
    res = client.get(loan_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(loan_permissions_url)
    assert res.status_code == 403

    # Logged as system librarian
    #   * sys_lib can 'list' and 'read' all loans
    #   * sys_lib can't 'read' 'update', 'delete' loans
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(loan_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(loan_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(loan_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']
    assert not data['delete']['can']


def test_loan_permissions(patron_martigny,
                          librarian_martigny,
                          system_librarian_martigny,
                          loan_overdue_saxon, loan_overdue_martigny,
                          loan_overdue_sion, org_martigny):
    """Test library permissions class."""

    # Anonymous user
    assert not LoanPermission.list(None, {})
    assert not LoanPermission.read(None, {})
    assert not LoanPermission.create(None, {})
    assert not LoanPermission.update(None, {})
    assert not LoanPermission.delete(None, {})

    loan_martigny = loan_overdue_martigny
    loan_saxon = loan_overdue_saxon
    loan_sion = loan_overdue_sion
    # As Patron
    with mock.patch(
        'rero_ils.modules.loans.permissions.current_patron',
        patron_martigny
    ), mock.patch(
        'rero_ils.modules.loans.permissions.current_organisation',
        org_martigny
    ):
        assert LoanPermission.list(None, loan_martigny)
        assert LoanPermission.read(None, loan_martigny)
        assert not LoanPermission.create(None, loan_martigny)
        assert not LoanPermission.update(None, loan_martigny)
        assert not LoanPermission.delete(None, loan_martigny)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.loans.permissions.current_patron',
        system_librarian_martigny
    ), mock.patch(
        'rero_ils.modules.loans.permissions.current_organisation',
        org_martigny
    ):
        assert LoanPermission.list(None, loan_saxon)
        assert LoanPermission.read(None, loan_saxon)
        assert not LoanPermission.create(None, loan_saxon)
        assert not LoanPermission.update(None, loan_saxon)
        assert not LoanPermission.delete(None, loan_saxon)

        assert LoanPermission.list(None, loan_sion)
        assert not LoanPermission.read(None, loan_sion)
        assert not LoanPermission.create(None, loan_sion)
        assert not LoanPermission.update(None, loan_sion)
        assert not LoanPermission.delete(None, loan_sion)
