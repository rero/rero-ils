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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""""Test permissions."""

from invenio_accounts.testutils import login_user_via_view
from utils import login_user_for_view

from rero_ils.permissions import can_access_item


def test_can_access_item_librarian(
        client, json_header,
        librarian_martigny_no_email, item_lib_martigny):
    """Test a librarian can access an item."""
    user = librarian_martigny_no_email.user
    assert not can_access_item(user=user)
    login_user_for_view(client, librarian_martigny_no_email)
    assert not can_access_item(user=user)
    assert can_access_item(user=user, item=item_lib_martigny)


def test_can_access_item_patron(
        client, json_header,
        patron_martigny_no_email, item_lib_martigny):
    """Test a patron can access an item."""

    login_user_for_view(client, patron_martigny_no_email)
    assert not can_access_item()
    assert not can_access_item(item=item_lib_martigny)


def test_can_access_item_no_user(
        client, json_header, item_lib_martigny):
    """Test can access an item no user."""
    assert not can_access_item()
    assert not can_access_item(item=item_lib_martigny)
