# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import current_app, url_for
from flask_principal import AnonymousIdentity, identity_changed
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.vendors.permissions import VendorPermissionPolicy
from tests.utils import check_permission, get_json


def test_vendor_permissions_api(
    client,
    org_sion,
    patron_martigny,
    system_librarian_martigny,
    vendor_martigny,
    vendor_sion,
):
    """Test organisations permissions api."""
    vendor_permissions_url = url_for("api_blueprint.permissions", route_name="vendors")
    vendor_martigny_permission_url = url_for(
        "api_blueprint.permissions",
        route_name="vendors",
        record_pid=vendor_martigny.pid,
    )
    vendor_sion_permission_url = url_for("api_blueprint.permissions", route_name="vendors", record_pid=vendor_sion.pid)

    # Not logged
    res = client.get(vendor_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(vendor_permissions_url)
    assert res.status_code == 403

    # Logged as system librarian
    #   * sys_lib can do everything about vendors of its own organisation
    #   * sys_lib can't do anything about vendors of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(vendor_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ["list", "read", "create", "update", "delete"]:
        assert data[action]["can"]

    res = client.get(vendor_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ["read", "update", "delete"]:
        assert not data[action]["can"]


def test_vendor_permissions(
    patron_martigny,
    librarian_martigny,
    librarian2_martigny,
    system_librarian_martigny,
    org_martigny,
    org_sion,
    vendor_martigny,
    vendor_sion,
):
    """Test vendor permissions class."""

    # Anonymous user
    #   - all actions is denied
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        VendorPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        {},
    )
    # Patron user
    #   - all actions is denied
    login_user(patron_martigny.user)
    check_permission(
        VendorPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        org_martigny,
    )
    # Full permission user
    #     - Allow all action on any vendor despite organisation owner
    login_user(system_librarian_martigny.user)
    check_permission(
        VendorPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        org_martigny,
    )
    # check permissions on other organisation
    check_permission(
        VendorPermissionPolicy,
        {"read": False, "create": False, "update": False, "delete": False},
        org_sion,
    )
    # Librarian with acquisition manager role
    #   - Allow all action on any vendor despite organisation owner
    login_user(librarian_martigny.user)
    check_permission(
        VendorPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        org_martigny,
    )
    # check permissions on other organisation
    check_permission(
        VendorPermissionPolicy,
        {"read": False, "create": False, "update": False, "delete": False},
        org_sion,
    )
    # Librarian without acquisition manager role
    # - can read vendors
    login_user(librarian2_martigny.user)
    check_permission(
        VendorPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        org_martigny,
    )
