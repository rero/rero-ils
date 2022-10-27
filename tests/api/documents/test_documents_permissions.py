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
from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from utils import check_permission, flush_index

from rero_ils.modules.documents.permissions import DocumentPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch


@mock.patch.object(Patron, '_extensions', [])
def test_documents_permissions(
    patron_martigny, librarian_martigny, document
):
    """Test documents permissions class."""
    # Anonymous user & Patron user
    #  - search/read any document are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(DocumentPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(DocumentPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, document)
    login_user(patron_martigny.user)
    check_permission(DocumentPermissionPolicy, {'create': False}, {})
    check_permission(DocumentPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, document)

    # Librarian with specific role
    #     - search/read: any document
    #     - create/update/delete: allowed for any document
    login_user(librarian_martigny.user)
    check_permission(DocumentPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, document)

    # Librarian without specific role
    #   - search/read: any document
    #   - create/update/delete: disallowed for any document !!
    original_roles = librarian_martigny.get('roles', [])
    librarian_martigny['roles'] = ['pro_circulation_manager']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(DocumentPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, document)

    # reset the librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    # Test if the document cannot be edited (harvested documents, ...)
    with mock.patch('rero_ils.modules.documents.api.Document.can_edit', False):
        check_permission(DocumentPermissionPolicy, {
            'search': True,
            'read': True,
            'create': False,
            'update': False,
            'delete': False
        }, document)
