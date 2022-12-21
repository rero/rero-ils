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

""""Test permissions."""
from utils import login_user_for_view

from rero_ils.modules.permissions import has_superuser_access
from rero_ils.permissions import librarian_update_permission_factory


def test_has_superuser_access(app):
    """Test permissions of has_superuser_access functions."""
    assert not has_superuser_access()
    app.config['RERO_ILS_APP_DISABLE_PERMISSION_CHECKS'] = True
    assert has_superuser_access()


def test_librarian_update_permission_factory(client, document, ebook_1,
                                             librarian_martigny,
                                             default_user_password):
    """Test librarian_update_permission_factory function."""
    assert not librarian_update_permission_factory(ebook_1).can()
    login_user_for_view(client, librarian_martigny, default_user_password)
    assert librarian_update_permission_factory(document).can()
