# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Commons RERO-ILS REST API."""

from unittest import mock

from flask import url_for
from flask_principal import Identity, RoleNeed
from invenio_access import ActionUsers, Permission
from invenio_accounts.models import Role
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.acquisition.budgets.permissions import (
    search_action as budget_search_action,
)
from rero_ils.modules.permissions import PermissionContext, can_use_debug_mode
from rero_ils.modules.receivers import process_boosting
from rero_ils.modules.users.models import UserRole
from rero_ils.permissions import librarian_delete_permission_factory
from tests.utils import get_json, mock_response, postdata


def test_librarian_delete_permission_factory(client, librarian_fully, org_martigny, lib_martigny):
    """Test librarian_delete_permission_factory"""
    login_user_via_session(client, librarian_fully.user)
    assert isinstance(librarian_delete_permission_factory(None, credentials_only=True), Permission)
    assert librarian_delete_permission_factory(org_martigny) is not None


def test_get_roles_management_permissions(client, system_librarian_martigny, patron_martigny, librarian_fully, app):
    """Test system_librarian permissions."""
    role_url = url_for("api_patrons.get_roles_management_permissions")
    res = client.get(role_url)
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)
    res = client.get(role_url)
    assert res.status_code == 403

    # Login as system_librarian
    login_user_via_session(client, system_librarian_martigny.user)
    # can manage all types of patron roles
    res = client.get(role_url)
    assert res.status_code == 200
    data = get_json(res)
    assert set(data["allowed_roles"]) == set(UserRole.ALL_ROLES)

    # Login as user manager
    login_user_via_session(client, librarian_fully.user)
    res = client.get(role_url)
    assert res.status_code == 200
    data = get_json(res)
    assert set(data["allowed_roles"]) == {UserRole.PATRON}


def test_permission_exposition(app, db, client, system_librarian_martigny):
    """Test permission exposition."""
    login_user_via_session(client, system_librarian_martigny.user)

    # test exposition by role =================================================
    res = client.get(url_for("api_blueprint.permissions_by_role", role="dummy-role"))
    data = get_json(res)
    assert res.status_code == 200
    assert not data

    res = client.get(url_for("api_blueprint.permissions_by_role", role=UserRole.PROFESSIONAL_READ_ONLY))
    data = get_json(res)
    assert res.status_code == 200
    assert UserRole.PROFESSIONAL_READ_ONLY in data

    res = client.get(url_for("api_blueprint.permissions_by_role", role=UserRole.PROFESSIONAL_ROLES))
    data = get_json(res)
    assert res.status_code == 200
    assert all(role in data for role in UserRole.PROFESSIONAL_ROLES)

    # test exposition by patron ===============================================
    res = client.get(
        url_for(
            "api_blueprint.permissions_by_patron",
            patron_pid=system_librarian_martigny.pid,
        )
    )
    data = get_json(res)
    assert res.status_code == 200
    assert len(data) == len(app.extensions["invenio-access"].actions)

    # system librarian should access to 'can-use-debug-mode'
    perm = next(p for p in data if p["name"] == can_use_debug_mode.value)
    assert perm["can"]
    # add a restriction specific for this user
    db.session.add(ActionUsers.deny(can_use_debug_mode, user_id=system_librarian_martigny.user.id))
    db.session.commit()
    res = client.get(
        url_for(
            "api_blueprint.permissions_by_patron",
            patron_pid=system_librarian_martigny.pid,
        )
    )
    data = get_json(res)
    assert res.status_code == 200
    perm = next(p for p in data if p["name"] == can_use_debug_mode.value)
    assert not perm["can"]
    # reset DB
    ActionUsers.query_by_action(can_use_debug_mode).filter(
        ActionUsers.user_id == system_librarian_martigny.user.id
    ).delete(synchronize_session=False)
    db.session.commit()


def test_permission_management(client, system_librarian_martigny):
    """Test permission management."""

    # Test bad usage of the API
    #   1) Anonymous user can't manage permissions.
    #   2) try with bad payload data
    #   3) try with not implemented context
    #   4) try with bad parameters
    res, _ = postdata(client, "api_blueprint.permission_management", {})
    assert res.status_code == 401

    login_user_via_session(client, system_librarian_martigny.user)
    res, data = postdata(client, "api_blueprint.permission_management", {})
    assert res.status_code == 400
    assert "context" in data["message"]
    res, data = postdata(
        client,
        "api_blueprint.permission_management",
        {
            "context": PermissionContext.BY_ROLE,
            "permission": budget_search_action.value,
        },
    )
    assert res.status_code == 400
    assert "role_name" in data["message"]

    res, data = postdata(
        client,
        "api_blueprint.permission_management",
        {"context": PermissionContext.BY_USER, "permission": budget_search_action.value},
    )
    assert res.status_code == 501

    res, data = postdata(
        client,
        "api_blueprint.permission_management",
        {
            "context": PermissionContext.BY_ROLE,
            "permission": "unknown-permission",
            "role_name": UserRole.PROFESSIONAL_READ_ONLY,
        },
    )
    assert res.status_code == 400
    assert "not found" in data["message"]
    res, data = postdata(
        client,
        "api_blueprint.permission_management",
        {
            "context": PermissionContext.BY_ROLE,
            "permission": budget_search_action.value,
            "role_name": "dummy-role",
        },
    )
    assert res.status_code == 400
    assert "not found" in data["message"]

    # Real test begin now
    #  1) test user has permission
    #  2) delete this permission using API and test the permission
    #  3) add the permission using API and test it again.
    role = Role.query.filter_by(name=UserRole.PROFESSIONAL_READ_ONLY).one()
    fake_identity = Identity("fake-id")
    fake_identity.provides.add(RoleNeed(role.id))
    permission = Permission(budget_search_action)
    assert fake_identity.can(permission)

    perm_url = url_for("api_blueprint.permission_management")
    perm_data = {
        "context": PermissionContext.BY_ROLE,
        "permission": budget_search_action.value,
        "role_name": UserRole.PROFESSIONAL_READ_ONLY,
    }
    res = client.delete(perm_url, json=perm_data)
    assert res.status_code == 204
    assert not fake_identity.can(permission)

    res = client.post(perm_url, json=perm_data)
    assert res.status_code == 200
    assert fake_identity.can(permission)


@mock.patch("rero_ils.modules.decorators.login_and_librarian", mock.MagicMock())
@mock.patch("requests.get")
def test_proxy(mock_get, client):
    """Test proxy."""
    response = client.get(url_for("api_blueprint.proxy"))
    assert response.status_code == 400
    assert response.json["message"] == "Missing `url` parameter"

    mock_get.return_value = mock_response(status=418)
    response = client.get(url_for("api_blueprint.proxy", url="http://mocked.url"))
    assert response.status_code == 418


def test_wiki_not_registered_on_api_app(app, client):
    """Test the wiki is not served by the API app."""
    assert "wiki.page" not in app.view_functions
    assert client.get("/help/home/").status_code == 404


def test_boosting_fields(app):
    """Test the boosting configuration."""
    # the configuration should exists
    assert app.config.get("RERO_ILS_QUERY_BOOSTING")

    # several cases of configurations
    assert process_boosting("documents", ["title.*"]) == ["title.*"]
    assert "title.*" in process_boosting("documents", ["*"])
    assert "title.*^2" in process_boosting("documents", ["title.*^2", "*"])
    # test fields
    assert "fulltext" in process_boosting("documents", ["*"])
    assert "fulltext.*" in process_boosting("documents", ["*"])
