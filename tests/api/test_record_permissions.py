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

"""Test record permissions API."""


from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json


def test_document_permissions(
        client, document, librarian_martigny_no_email,
        patron_martigny_no_email, ebook_1, circ_policy_short_martigny):
    """Test document permissions."""
    # failed: invlaid document pid is given
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='documents',
            record_pid='no_pid'
        )
    )
    assert res.status_code == 401
    # failed: no logged user
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='documents',
            record_pid=document.pid
        )
    )
    assert res.status_code == 401

    # failed: logged patron and a valid document pid is given
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='documents',
            record_pid=document.pid
        )
    )
    assert res.status_code == 403

    # success: logged user and a valid document pid is given
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='documents',
            record_pid=document.pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert 'update' in data
    assert 'delete' in data

    # success: logged user and a valid document pid is given
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='documents',
            record_pid=ebook_1.pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert 'update' in data
    assert 'delete' in data

    # failed: invlaid route name
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='no_route',
            record_pid=document.pid
        )
    )
    assert res.status_code == 400

    # failed: permission denied
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='circ_policies',
            record_pid=circ_policy_short_martigny.pid
        )
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('delete', {}).get('can') is False
    reasons = data.get('delete', {}).get('reasons', {})
    assert 'others' in reasons and 'permission' in reasons['others']
