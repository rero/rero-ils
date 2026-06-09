# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Tests REST API operation logs."""

import json
from copy import deepcopy
from datetime import datetime
from unittest import mock

from flask import current_app, url_for
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.files.cli import create_pdf_record_files
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.operation_logs.api import OperationLog, OperationLogsSearch
from rero_ils.modules.operation_logs.models import OperationLogOperation
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.utils import create_patron_from_data
from rero_ils.modules.utils import get_ref_for_pid
from tests.utils import VerifyRecordPermissionPatch, get_json, postdata


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_operation_logs_permissions(
    client,
    operation_log,
    librarian_martigny,
    patron_martigny,
    librarian_patron_martigny,
    json_header,
):
    """Test operation logs permissions."""
    item_list = url_for("invenio_records_rest.oplg_list")

    # Check access for librarian role
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    librarian_count = data["hits"]["total"]["value"]
    assert librarian_count > 0

    # Check access for patron role
    login_user_via_session(client, patron_martigny.user)
    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 0

    # Check access for patron and librarian roles
    login_user_via_session(client, librarian_patron_martigny.user)
    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"]["value"] == librarian_count


def test_operation_logs_rest(
    client,
    loan_pending_martigny,
    librarian_martigny,
    json_header,
    loan_overdue_martigny,
):
    """Test operation logs REST API."""
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.oplg_item", pid_value="1")
    item_list = url_for("invenio_records_rest.oplg_list")

    res = client.get(item_url)
    assert res.status_code == 404

    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"]["value"] > 0
    pid = data["hits"]["hits"][0]["metadata"]["pid"]
    assert pid
    assert data["hits"]["hits"][0]["id"] == pid
    assert data["hits"]["hits"][0]["created"]
    assert data["hits"]["hits"][0]["updated"]

    res, _ = postdata(client, "invenio_records_rest.oplg_list", {})
    assert res.status_code == 403

    res = client.put(
        url_for("invenio_records_rest.oplg_item", pid_value="1"),
        data={},
        headers=json_header,
    )
    assert res.status_code == 404

    res = client.delete(item_url)
    assert res.status_code == 404


def test_operation_log_on_item(
    client,
    item_lib_martigny_data_tmp,
    librarian_martigny,
    json_header,
    item_lib_martigny,
):
    """Test operation log on Item."""

    # STEP #1 : Create an item. This will generate an operation log
    item_data = deepcopy(item_lib_martigny_data_tmp)
    del item_data["pid"]
    item = Item.create(item_data, dbcommit=True, reindex=True)
    OperationLogsSearch.flush_and_refresh()

    q = f"record.type:item AND record.value:{item.pid}"
    search_url = url_for("invenio_records_rest.oplg_list", q=q, sort="mostrecent")
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
    metadata = data["hits"]["hits"][0]["metadata"]
    assert metadata["operation"] == OperationLogOperation.CREATE

    # STEP #2 : Update the item ``price`` attribute.
    #   As any changes on this attribute must be logged, a new operation log
    #   will be generated.
    item["price"] = 10
    item = item.update(item, dbcommit=True, reindex=True)
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 2
    metadata = data["hits"]["hits"][0]["metadata"]
    assert metadata["operation"] == OperationLogOperation.UPDATE

    # STEP #3 : Update the item ``status`` attribute.
    #   This attribute doesn't need to be tracked. So if it's the only change
    #   on this record then no OpLog should be created.
    item["status"] = ItemStatus.EXCLUDED
    item = item.update(item, dbcommit=True, reindex=True)
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 2

    # STEP #4 : Update the item ``status`` and ``price`` attributes.
    #   As we update at least one attribute that need to be tracked, this
    #   update will generate a new OpLog (UPDATE)
    item["status"] = ItemStatus.AT_DESK
    item["price"] = 12
    item = item.update(item, dbcommit=True, reindex=True)
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 3
    metadata = data["hits"]["hits"][0]["metadata"]
    assert metadata["operation"] == OperationLogOperation.UPDATE

    # STEP #5 : Delete the item
    #   This will generate the last OpLog about the item.
    item.delete(dbcommit=True, delindex=True)
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 4
    metadata = data["hits"]["hits"][0]["metadata"]
    assert metadata["operation"] == OperationLogOperation.DELETE


def test_operation_log_on_patron(
    app,
    client,
    roles,
    lib_martigny,
    patron_type_children_martigny,
    patron_martigny_data_tmp,
    librarian_martigny,
    json_header,
):
    """Test operation log on Patron."""
    patron_data = deepcopy(patron_martigny_data_tmp)
    patron_data["email"] = "oplg_patron@test.ch"
    patron_data["username"] = "oplg_patron"
    patron_data["patron"]["barcode"] = ["oplg_patron_barcode"]
    del patron_data["pid"]

    # STEP #1: Create a patron -> generates a CREATE operation log
    patron = create_patron_from_data(patron_data)
    OperationLogsSearch.flush_and_refresh()

    login_user_via_session(client, librarian_martigny.user)
    q = f"record.type:ptrn AND record.value:{patron.pid}"
    search_url = url_for("invenio_records_rest.oplg_list", q=q, sort="mostrecent")
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
    assert data["hits"]["hits"][0]["metadata"]["operation"] == OperationLogOperation.CREATE

    # STEP #2: Update the patron -> generates an UPDATE operation log
    patron["patron"]["barcode"] = ["oplg_patron_barcode_updated"]
    patron.update(patron, dbcommit=True, reindex=True)
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 2
    assert data["hits"]["hits"][0]["metadata"]["operation"] == OperationLogOperation.UPDATE

    # STEP #2bis: Update through the REST API (PUT) -> a single UPDATE log.
    #   The REST handler calls ``record.update(data)`` then ``record.commit()``.
    #   ``Patron.update`` must not commit by itself, otherwise the operation
    #   log would be written twice for one PUT.
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron.pid)
    put_data = deepcopy(dict(patron))
    put_data["patron"]["barcode"] = ["oplg_patron_barcode_put"]
    res = client.put(item_url, data=json.dumps(put_data), headers=json_header)
    assert res.status_code == 200
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 3
    assert data["hits"]["hits"][0]["metadata"]["operation"] == OperationLogOperation.UPDATE

    # STEP #3: Delete the patron -> generates a DELETE operation log
    #   Reload the record as the PUT above bumped its revision server-side.
    patron = Patron.get_record_by_pid(patron.pid)
    user_id = patron["user_id"]
    patron.delete(dbcommit=True, delindex=True)
    OperationLogsSearch.flush_and_refresh()

    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 4
    assert data["hits"]["hits"][0]["metadata"]["operation"] == OperationLogOperation.DELETE

    ds = app.extensions["invenio-accounts"].datastore
    ds.delete_user(ds.find_user(id=user_id))


def test_operation_log_on_ill_request(client, ill_request_martigny, librarian_martigny):
    """Test operation log on ILL request."""
    # Using the ``ill_request_martigny`` fixtures, an operation log is created
    # for 'create' operation. Check this operation log to check if special
    # additional informations are included into this OpLog.
    login_user_via_session(client, librarian_martigny.user)

    fake_data = {"date": datetime.now().isoformat()}
    oplg_index = OperationLog.get_index(fake_data)
    OperationLogsSearch.flush_and_refresh()

    q = f"record.type:illr AND record.value:{ill_request_martigny.pid}"
    search_url = url_for("invenio_records_rest.oplg_list", q=q, sort="mostrecent")
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
    metadata = data["hits"]["hits"][0]["metadata"]
    assert metadata["operation"] == OperationLogOperation.CREATE
    assert "ill_request" in metadata
    assert "status" in metadata["ill_request"]


def test_operation_log_on_file(client, librarian_martigny, document, lib_martigny, file_location):
    """Test files operation log."""

    # get the op index
    fake_data = {"date": datetime.now().isoformat()}
    oplg_index = OperationLog.get_index(fake_data)

    # create a pdf file
    metadata = {
        "library": {"$ref": get_ref_for_pid("lib", lib_martigny.pid)},
        "collections": ["col1", "col2"],
    }
    record = create_pdf_record_files(document, metadata)
    recid = record["id"]

    # get services
    ext = current_app.extensions["rero-invenio-files"]
    file_service = ext.records_files_service
    record_service = ext.records_service

    # flush indices
    DocumentsSearch.flush_and_refresh()
    OperationLogsSearch.flush_and_refresh()

    # REST API are restricted, thus it needs a login
    login_user_via_session(client, librarian_martigny.user)

    # record file creation is in the op
    search_url = url_for("invenio_records_rest.oplg_list", q="record.type:recid AND operation:create")
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
    metadata = data["hits"]["hits"][0]["metadata"]
    assert set(metadata["record"].keys()) == {"library_pid", "organisation_pid", "type", "value"}
    assert set(metadata["file"]["document"]) == {"pid", "type", "title"}

    # record file update is in the op
    record_service.update(system_identity, recid, {"metadata": record["metadata"]})
    OperationLogsSearch.flush_and_refresh()
    search_url = url_for("invenio_records_rest.oplg_list", q="record.type:recid AND operation:update")
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1

    # file creation is in the op
    pdf_file_name = "doc_doc1_1.pdf"
    search_url = url_for(
        "invenio_records_rest.oplg_list",
        q=f"record.type:file AND operation:create AND record.value:{pdf_file_name}",
    )
    res = client.get(search_url)
    data = get_json(res)
    metadata = data["hits"]["hits"][0]["metadata"]
    assert data["hits"]["total"]["value"] == 1
    assert set(data["hits"]["hits"][0]["metadata"]["record"].keys()) == {
        "library_pid",
        "organisation_pid",
        "type",
        "value",
    }
    assert set(metadata["file"]["document"]) == {"pid", "type", "title"}
    assert metadata["file"]["recid"] == recid

    # file deletion is in the op
    file_service.delete_file(identity=system_identity, id_=recid, file_key=pdf_file_name)
    OperationLogsSearch.flush_and_refresh()

    search_url = url_for(
        "invenio_records_rest.oplg_list",
        q=f"record.type:file AND operation:delete AND record.value:{pdf_file_name}",
    )
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1

    # record file deletion is in the op
    record_service.delete(identity=system_identity, id_=recid)
    OperationLogsSearch.flush_and_refresh()
    search_url = url_for("invenio_records_rest.oplg_list", q="record.type:recid AND operation:delete")
    res = client.get(search_url)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
