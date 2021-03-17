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

from rero_ils.modules.patrons.permissions import PatronPermission


def test_patrons_permissions(patron_martigny,
                             librarian_martigny,
                             system_librarian_martigny,
                             org_martigny, librarian_saxon,
                             patron_sion):
    """Test patrons permissions class."""

    sys_lib = system_librarian_martigny
    # Anonymous user
    assert not PatronPermission.list(None, {})
    assert not PatronPermission.read(None, {})
    assert not PatronPermission.create(None, {})
    assert not PatronPermission.update(None, {})
    assert not PatronPermission.delete(None, {})

    # As Librarian
    with mock.patch(
        'rero_ils.modules.patrons.permissions.current_librarian',
        librarian_martigny
    ):
        assert PatronPermission.list(None, patron_martigny)
        assert PatronPermission.read(None, patron_martigny)
        assert PatronPermission.create(None, patron_martigny)
        assert PatronPermission.update(None, patron_martigny)
        assert PatronPermission.delete(None, patron_martigny)

        assert PatronPermission.read(None, librarian_saxon)
        assert not PatronPermission.create(None, librarian_saxon)
        assert not PatronPermission.update(None, librarian_saxon)
        assert not PatronPermission.delete(None, librarian_saxon)

        assert not PatronPermission.read(None, patron_sion)
        assert not PatronPermission.create(None, patron_sion)
        assert not PatronPermission.update(None, patron_sion)
        assert not PatronPermission.delete(None, patron_sion)

        assert not PatronPermission.create(None, sys_lib)
        assert not PatronPermission.update(None, sys_lib)
        assert not PatronPermission.delete(None, sys_lib)

        assert not PatronPermission.delete(None, librarian_martigny)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.patrons.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert PatronPermission.list(None, librarian_saxon)
        assert PatronPermission.read(None, librarian_saxon)
        assert PatronPermission.create(None, librarian_saxon)
        assert PatronPermission.update(None, librarian_saxon)
        assert PatronPermission.delete(None, librarian_saxon)

        assert not PatronPermission.read(None, patron_sion)
        assert not PatronPermission.create(None, patron_sion)
        assert not PatronPermission.update(None, patron_sion)
        assert not PatronPermission.delete(None, patron_sion)

        assert not PatronPermission.delete(None, sys_lib)
