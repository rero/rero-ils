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

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.contributions.permissions import ContributionPermission


def test_contribution_permissions_api(client, patron_martigny,
                                      contribution_person,
                                      librarian_martigny):
    """Test organisations permissions api."""
    prs_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='contributions'
    )
    prs_real_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='contributions',
        record_pid=contribution_person.pid
    )

    # Not logged
    res = client.get(prs_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(prs_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(prs_real_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_contribution_permissions():
    """Test contribution permissions class."""

    assert ContributionPermission.list(None, {})
    assert ContributionPermission.read(None, {})
    assert not ContributionPermission.create(None, {})
    assert not ContributionPermission.update(None, {})
    assert not ContributionPermission.delete(None, {})
