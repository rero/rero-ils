# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Marshmallow schema through REST API for templates."""

import json
from copy import deepcopy
from unittest import mock

from flask import url_for

from rero_ils.modules.templates.api import Template
from rero_ils.modules.templates.models import TemplateVisibility
from tests.utils import VerifyRecordPermissionPatch, login_user_via_session, postdata


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_templates_marshmallow_loaders(
    client, system_librarian_martigny, templ_doc_public_martigny_data_tmp, json_header
):
    """Test template marshmallow loaders"""
    login_user_via_session(client, system_librarian_martigny.user)
    data = templ_doc_public_martigny_data_tmp
    del data["pid"]

    # TEST#1 :: API vs Console mode
    #   Through the API, a public template creation aren't allowed.
    #   Public template must be created as `private` and updated later by
    #   an authorized staff member. But using console mode, such restriction
    #   aren't applicable.
    assert data["visibility"] == TemplateVisibility.PUBLIC
    res, res_data = postdata(client, "invenio_records_rest.tmpl_list", data)
    assert res.status_code == 400

    template = Template.create(deepcopy(data), dbcommit=True, reindex=False)
    assert template.pid
    template.delete()

    # TEST#2 :: API workflow
    #   Create a private template using API, then update it to set visibility
    #   as 'public'.
    data["visibility"] = TemplateVisibility.PRIVATE
    res, res_data = postdata(client, "invenio_records_rest.tmpl_list", data)
    assert res.status_code == 201

    data["pid"] = res_data["metadata"]["pid"]
    data["visibility"] = TemplateVisibility.PUBLIC
    res = client.put(
        url_for("invenio_records_rest.tmpl_item", pid_value=data["pid"]),
        data=json.dumps(data),
        headers=json_header,
    )
    assert res.status_code == 200
    template = Template.get_record_by_pid(data["pid"])
    assert template.is_public

    # RESET FIXTURES
    template.delete()
