# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Utils for acquisitions."""
import mock
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
    else:
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
