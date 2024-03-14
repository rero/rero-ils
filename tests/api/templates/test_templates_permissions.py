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

from rero_ils.modules.patrons.api import Patron, PatronsSearch
from rero_ils.modules.templates.permissions import TemplatePermissionPolicy


@mock.patch.object(Patron, '_extensions', [])
def test_template_permissions(
    patron_martigny, librarian_martigny, system_librarian_martigny,
    org_martigny, templ_doc_public_martigny, templ_doc_private_martigny,
    templ_doc_public_sion, templ_doc_private_saxon, templ_doc_public_saxon,
    templ_doc_private_sion
):
    """Test template permissions class."""

    # Anonymous user & Patron user
    #  - None operation are allowed
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(TemplatePermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(TemplatePermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_martigny)
    login_user(patron_martigny.user)
    check_permission(TemplatePermissionPolicy, {'create': False}, {})
    check_permission(TemplatePermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_sion)

    # Librarian with only 'read_only' role
    #     - search/read: templates for its own organisation
    #     - create/update/delete: disallowed
    original_roles = librarian_martigny.get('roles', [])
    librarian_martigny['roles'] = ['pro_read_only']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_private_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_sion)

    # Librarian with classic 'staff-member' role:
    #   * public template :
    #     - search/read: templates of its own organisation
    #     - create/update/delete: disallowed operations
    #   * private templates :
    #     - all operations available only for its own templates.
    librarian_martigny['roles'] = ['pro_circulation_manager']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_sion)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, templ_doc_private_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_private_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_private_sion)

    # Librarian with classic 'library-administration' role:
    #   * public template (same other staff-members):
    #     - search/read: templates of its own organisation
    #     - create/update/delete: disallowed operations
    #   * private templates :
    #     - read: all templates linked to its own library
    #     - other operations available only for its own templates.
    librarian_martigny['roles'] = ['pro_library_administrator']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_sion)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, templ_doc_private_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_private_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_private_sion)

    # Librarian with classic 'full-permissions' role:
    #   * public and private templates:
    #     - all operations for templates in their own organisation
    librarian_martigny['roles'] = ['pro_full_permissions']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, templ_doc_public_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, templ_doc_public_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_public_sion)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, templ_doc_private_martigny)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, templ_doc_private_saxon)
    check_permission(TemplatePermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, templ_doc_private_sion)

    # reset librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)
