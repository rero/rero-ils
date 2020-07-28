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

from rero_ils.modules.persons.permissions import PersonPermission


def test_person_permissions_api(client, patron_martigny_no_email, person,
                                librarian_martigny_no_email):
    """Test organisations permissions api."""
    prs_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='persons'
    )
    prs_real_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='persons',
        record_pid=person.pid
    )

    # Not logged
    res = client.get(prs_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(prs_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(prs_real_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_person_permissions():
    """Test person permissions class."""

    assert PersonPermission.list(None, {})
    assert PersonPermission.read(None, {})
    assert not PersonPermission.create(None, {})
    assert not PersonPermission.update(None, {})
    assert not PersonPermission.delete(None, {})
