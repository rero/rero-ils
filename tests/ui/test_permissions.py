# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test permissions."""

from utils import login_user
from rero_ils.permissions import can_access_item


def test_can_access_item_librarian(
        client, json_header,
        librarian_martigny_no_email, item_lib_martigny):
    """Test a librarian can access an item."""

    assert not can_access_item()
    login_user(client, librarian_martigny_no_email)
    assert not can_access_item()
    assert can_access_item(item=item_lib_martigny)


def test_can_access_item_patron(
        client, json_header,
        patron_martigny_no_email, item_lib_martigny):
    """Test a patron can access an item."""

    login_user(client, patron_martigny_no_email)
    assert not can_access_item()
    assert not can_access_item(item=item_lib_martigny)


def test_can_access_item_no_user(
        client, json_header, item_lib_martigny):
    """Test can access an item no user."""
    assert not can_access_item()
    assert not can_access_item(item=item_lib_martigny)
