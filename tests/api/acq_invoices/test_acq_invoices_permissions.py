# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.acq_invoices.permissions import AcqInvoicePermission


def test_invoice_permissions_api(client, org_sion, patron_martigny,
                                 system_librarian_martigny,
                                 librarian_martigny,
                                 acq_invoice_fiction_martigny,
                                 acq_invoice_fiction_saxon,
                                 acq_invoice_fiction_sion):
    """Test invoices permissions api."""
    invoice_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_invoices'
    )
    invoice_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_invoices',
        record_pid=acq_invoice_fiction_martigny.pid
    )
    invoice_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_invoices',
        record_pid=acq_invoice_fiction_saxon.pid
    )
    invoice_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_invoices',
        record_pid=acq_invoice_fiction_sion.pid
    )

    # Not logged
    res = client.get(invoice_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(invoice_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' invoices of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' invoices for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(invoice_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(invoice_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(invoice_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about invoices of its own organisation
    #   * sys_lib can't do anything about invoices of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(invoice_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(invoice_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_invoice_permissions(patron_martigny,
                             librarian_martigny,
                             system_librarian_martigny,
                             document, org_martigny,
                             acq_invoice_fiction_sion,
                             acq_invoice_fiction_saxon,
                             acq_invoice_fiction_martigny):
    """Test invoices permissions class."""

    # Anonymous user
    assert not AcqInvoicePermission.list(None, {})
    assert not AcqInvoicePermission.read(None, {})
    assert not AcqInvoicePermission.create(None, {})
    assert not AcqInvoicePermission.update(None, {})
    assert not AcqInvoicePermission.delete(None, {})

    # As non Librarian
    invoice_martigny = acq_invoice_fiction_martigny
    invoice_saxon = acq_invoice_fiction_saxon
    invoice_sion = acq_invoice_fiction_sion

    assert not AcqInvoicePermission.list(None, invoice_martigny)
    assert not AcqInvoicePermission.read(None, invoice_martigny)
    assert not AcqInvoicePermission.create(None, invoice_martigny)
    assert not AcqInvoicePermission.update(None, invoice_martigny)
    assert not AcqInvoicePermission.delete(None, invoice_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        librarian_martigny
    ):
        assert AcqInvoicePermission.list(None, invoice_martigny)
        assert AcqInvoicePermission.read(None, invoice_martigny)
        assert AcqInvoicePermission.create(None, invoice_martigny)
        assert AcqInvoicePermission.update(None, invoice_martigny)
        assert AcqInvoicePermission.delete(None, invoice_martigny)

        assert not AcqInvoicePermission.read(None, invoice_saxon)
        assert not AcqInvoicePermission.create(None, invoice_saxon)
        assert not AcqInvoicePermission.update(None, invoice_saxon)
        assert not AcqInvoicePermission.delete(None, invoice_saxon)

        assert not AcqInvoicePermission.read(None, invoice_sion)
        assert not AcqInvoicePermission.create(None, invoice_sion)
        assert not AcqInvoicePermission.update(None, invoice_sion)
        assert not AcqInvoicePermission.delete(None, invoice_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert AcqInvoicePermission.list(None, invoice_saxon)
        assert AcqInvoicePermission.read(None, invoice_saxon)
        assert AcqInvoicePermission.create(None, invoice_saxon)
        assert AcqInvoicePermission.update(None, invoice_saxon)
        assert AcqInvoicePermission.delete(None, invoice_saxon)

        assert not AcqInvoicePermission.read(None, invoice_sion)
        assert not AcqInvoicePermission.create(None, invoice_sion)
        assert not AcqInvoicePermission.update(None, invoice_sion)
        assert not AcqInvoicePermission.delete(None, invoice_sion)
