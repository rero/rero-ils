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
from utils import get_json, login_user


def test_document_permissions(
        client, document, librarian_martigny,
        patron_martigny, ebook_1, circ_policy_short_martigny):
    """Test document permissions."""
    # failed: invalid document pid is given
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
    login_user_via_session(client, patron_martigny.user)
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='documents',
            record_pid=document.pid
        )
    )
    assert res.status_code == 403

    # success: logged user and a valid document pid is given
    login_user_via_session(client, librarian_martigny.user)
    data = call_api_permissions(client, 'documents', document.pid)
    assert 'update' in data
    assert 'delete' in data

    # success: logged user and a valid document pid is given
    login_user_via_session(client, librarian_martigny.user)
    data = call_api_permissions(client, 'documents', ebook_1.pid)
    assert 'update' in data
    assert 'delete' in data

    # failed: invalid route name
    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='no_route',
            record_pid=document.pid
        )
    )
    assert res.status_code == 400

    # failed: permission denied
    data = call_api_permissions(client, 'circ_policies',
                                circ_policy_short_martigny.pid)
    assert data.get('delete', {}).get('can') is False
    reasons = data.get('delete', {}).get('reasons', {})
    assert 'others' in reasons and 'permission' in reasons['others']


def test_patrons_permissions(
    client,
    patron_martigny,
    librarian_martigny,
    librarian2_martigny,
    librarian_saxon,
    system_librarian_martigny,
    system_librarian2_martigny,
    system_librarian_sion,
    librarian_sion
):
    """Test permissions for patrons."""

    # simple librarian -----------------------------------------------
    login_user(client, librarian_martigny)
    # 1) should update and delete a librarian of the same library
    data = call_api_permissions(client, 'patrons', librarian2_martigny.pid)
    assert data['delete']['can']
    assert data['update']['can']
    # 2) should not update and delete a librarian of an other library
    data = call_api_permissions(client, 'patrons', librarian_saxon.pid)
    assert not data['delete']['can']
    assert not data['update']['can']
    # 3) should not delete a system librarian
    #    but can update it (except some roles management)
    data = call_api_permissions(client, 'patrons',
                                system_librarian_martigny.pid)
    assert not data['delete']['can']
    assert data['update']['can']

    # system librarian ----------------------------------------------
    login_user(client, system_librarian_martigny)
    # should update and delete a librarian of the same library
    data = call_api_permissions(client, 'patrons', librarian2_martigny.pid)
    assert data['delete']['can']
    assert data['update']['can']

    # should update and delete a librarian of an other library
    data = call_api_permissions(client, 'patrons', librarian_saxon.pid)
    assert data['delete']['can']
    assert data['update']['can']

    # should update and delete a system librarian of the same organisation
    # but not itself
    data = call_api_permissions(client, 'patrons',
                                system_librarian2_martigny.pid)
    assert data['delete']['can']
    assert data['update']['can']

    # should not update and delete a system librarian of another organisation
    data = call_api_permissions(client, 'patrons', system_librarian_sion.pid)
    assert not data['delete']['can']
    assert not data['update']['can']


def test_items_permissions(
    client,
    item_lib_martigny,  # on shelf
    item_lib_fully,  # on loan
    librarian_martigny
):
    """Test record retrieval."""
    login_user(client, librarian_martigny)

    data = call_api_permissions(client, 'items', item_lib_fully.pid)
    assert not data['delete']['can']
    assert not data['update']['can']

    data = call_api_permissions(client, 'items', item_lib_martigny.pid)
    assert data['delete']['can']
    assert data['update']['can']

    response = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='items',
            record_pid='dummy_item_pid'
        )
    )
    assert response.status_code == 404


def call_api_permissions(client, route_name, pid):
    """Get permissions from permissions API."""
    response = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name=route_name,
            record_pid=pid
        )
    )
    assert response.status_code == 200
    return get_json(response)
