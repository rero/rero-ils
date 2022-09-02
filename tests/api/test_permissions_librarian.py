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

from invenio_access import Permission
from invenio_accounts.testutils import login_user_via_session

from rero_ils.permissions import librarian_delete_permission_factory


def test_librarian_delete_permission_factory(
        client, librarian_fully, org_martigny, lib_martigny):
    """Test librarian_delete_permission_factory """
    login_user_via_session(client, librarian_fully.user)
    assert type(librarian_delete_permission_factory(
        None,
        credentials_only=True
    )) == Permission
    assert librarian_delete_permission_factory(org_martigny) is not None
