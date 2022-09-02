# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Tests REST API patrons."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.users.models import UserRole


def test_system_librarian_permissions(
        client, json_header, system_librarian_martigny,
        patron_martigny, patron_type_adults_martigny,
        librarian_fully):
    """Test system_librarian permissions."""
    # Login as system_librarian
    login_user_via_session(client, system_librarian_martigny.user)

    # can manage all types of patron roles
    role_url = url_for('api_patrons.get_roles_management_permissions')
    res = client.get(role_url)
    assert res.status_code == 200
    data = get_json(res)
    assert UserRole.FULL_PERMISSIONS in data['allowed_roles']
