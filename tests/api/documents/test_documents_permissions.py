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
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.documents.permissions import DocumentPermission


def test_documents_permissions_api(client, document, ebook_1,
                                   system_librarian_martigny):
    """Test documents permissions api."""
    # Logged as system librarian.
    #   * All operation are allowed for normal document
    #   * Even a harvested document cannot be delete/edit
    doc_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='documents',
        record_pid=document.pid
    )
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(doc_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    doc_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='documents',
        record_pid=ebook_1.pid
    )
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(doc_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_documents_permissions(patron_martigny,
                               librarian_martigny,
                               document):
    """Test documents permissions class."""

    # Anonymous user
    assert DocumentPermission.list(None, document)
    assert DocumentPermission.read(None, document)
    assert not DocumentPermission.create(None, document)
    assert not DocumentPermission.update(None, document)
    assert not DocumentPermission.delete(None, document)

    # As non Librarian
    assert DocumentPermission.list(None, document)
    assert DocumentPermission.read(None, document)
    assert not DocumentPermission.create(None, document)
    assert not DocumentPermission.update(None, document)
    assert not DocumentPermission.delete(None, document)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.documents.permissions.current_librarian',
        librarian_martigny
    ):
        assert DocumentPermission.list(None, document)
        assert DocumentPermission.read(None, document)
        assert DocumentPermission.create(None, document)
        assert DocumentPermission.update(None, document)
        assert DocumentPermission.delete(None, document)
