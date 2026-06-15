# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utils for acquisitions."""

from unittest import mock

from flask import url_for

from rero_ils.modules.utils import get_record_class_from_schema_or_pid_type
from tests.utils import VerifyRecordPermissionPatch, postdata


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def _make_resource(client, pid_type, input_data):
    """Dynamic creation of resource using REST_API.

    :param client: the client to use to call the REST api.
    :param pid_type: the type of resource to create.
    :param input_data: the resource data.
    """
    record_class = get_record_class_from_schema_or_pid_type(pid_type=pid_type)
    url_alias = f"invenio_records_rest.{pid_type}_list"
    res, data = postdata(client, url_alias, input_data)
    if res.status_code == 201:
        return record_class.get_record_by_pid(data["metadata"]["pid"])
    raise Exception(data["message"])


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def _del_resource(client, pid_type, pid):
    """Delete a resource using the REST API.

    :param client: the client to use to call the REST api.
    :param pid_type: the type of resource to create.
    :param pid: resource pid to delete.
    """
    item_url = url_for(f"invenio_records_rest.{pid_type}_item", pid_value=pid)
    res = client.delete(item_url)
    assert res.status_code == 204
