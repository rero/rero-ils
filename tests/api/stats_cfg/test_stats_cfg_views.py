# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2022 UCLouvain
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

"""Stats views tests."""

from __future__ import absolute_import, print_function

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_view_stats_cfg(
        client, patron_martigny, librarian_martigny,
        system_librarian_martigny
):
    """Test view status."""
    # User not logged
    result = client.get(url_for('stats_cfg.live_stats_reports', pid='1'))
    assert result.status_code == 401

    # User without access permissions
    login_user_via_session(client, patron_martigny.user)
    result = client.get(url_for('stats_cfg.live_stats_reports', pid='1'))
    assert result.status_code == 403

    # User with librarian permissions
    login_user_via_session(client, librarian_martigny.user)
    result = client.get(url_for('stats_cfg.live_stats_reports', pid='1'))
    assert result.status_code == 403

    # User with librarian permissions
    login_user_via_session(client, system_librarian_martigny.user)
    result = client.get(url_for('stats_cfg.live_stats_reports', pid='foo'))
    assert result.status_code == 404
