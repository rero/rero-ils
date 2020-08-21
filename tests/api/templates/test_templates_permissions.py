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

from rero_ils.modules.templates.permissions import TemplatePermission


def test_templates_permissions_api(client, patron_martigny_no_email,
                                   templ_doc_private_martigny,
                                   templ_doc_public_martigny,
                                   librarian_martigny_no_email,
                                   templ_doc_public_sion,
                                   system_librarian_martigny_no_email):
    """Test templates permissions api."""
    template_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='templates'
    )
    templ_doc_pub_martigny_url = url_for(
        'api_blueprint.permissions',
        route_name='templates',
        record_pid=templ_doc_public_martigny.pid
    )
    templ_doc_private_martigny_url = url_for(
        'api_blueprint.permissions',
        route_name='templates',
        record_pid=templ_doc_private_martigny.pid
    )
    templ_sion_pub_url = url_for(
        'api_blueprint.permissions',
        route_name='templates',
        record_pid=templ_doc_public_sion.pid
    )

    # Not logged
    res = client.get(template_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(template_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(templ_doc_pub_martigny_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(templ_doc_private_martigny_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(templ_sion_pub_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(templ_doc_private_martigny_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(templ_sion_pub_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_template_permissions(
        patron_martigny_no_email, librarian_martigny_no_email,
        system_librarian_martigny_no_email, org_martigny,
        templ_doc_public_martigny, templ_doc_private_martigny,
        templ_doc_public_sion):
    """Test template permissions class."""

    # Anonymous user
    assert not TemplatePermission.list(None, {})
    assert not TemplatePermission.read(None, {})
    assert not TemplatePermission.create(None, {})
    assert not TemplatePermission.update(None, {})
    assert not TemplatePermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.templates.permissions.current_patron',
        patron_martigny_no_email
    ):
        assert not TemplatePermission.list(None, {})
        assert not TemplatePermission.read(None, {})
        assert not TemplatePermission.create(None, {})
        assert not TemplatePermission.update(None, {})
        assert not TemplatePermission.delete(None, {})

    # As Librarian
    with mock.patch(
        'rero_ils.modules.templates.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.templates.permissions.current_organisation',
        org_martigny
    ):
        assert TemplatePermission.list(None, templ_doc_public_martigny)
        assert TemplatePermission.read(None, templ_doc_public_martigny)
        assert not TemplatePermission.create(None, templ_doc_public_martigny)
        assert not TemplatePermission.update(None, templ_doc_public_martigny)
        assert not TemplatePermission.delete(None, templ_doc_public_martigny)

        assert TemplatePermission.list(None, templ_doc_public_sion)
        assert not TemplatePermission.read(None, templ_doc_public_sion)
        assert not TemplatePermission.create(None, templ_doc_public_sion)
        assert not TemplatePermission.update(None, templ_doc_public_sion)
        assert not TemplatePermission.delete(None, templ_doc_public_sion)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.templates.permissions.current_patron',
        system_librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.templates.permissions.current_organisation',
        org_martigny
    ):
        assert TemplatePermission.list(None, templ_doc_private_martigny)
        assert TemplatePermission.read(None, templ_doc_private_martigny)
        assert TemplatePermission.create(None, templ_doc_private_martigny)
        assert TemplatePermission.update(None, templ_doc_private_martigny)
        assert TemplatePermission.delete(None, templ_doc_private_martigny)

        assert not TemplatePermission.read(None, templ_doc_public_sion)
        assert not TemplatePermission.create(None, templ_doc_public_sion)
        assert not TemplatePermission.update(None, templ_doc_public_sion)
        assert not TemplatePermission.delete(None, templ_doc_public_sion)
