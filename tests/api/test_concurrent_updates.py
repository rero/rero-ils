# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for concurrent record update protection via ETag / If-Match.

Two behaviours are covered here:

* the 409 conflict response built by the error handler registered in ext.py, the
  only part of this protection still implemented in rero-ils;
* the weak ETag check of invenio-records-rest. Testing a dependency is normally
  out of scope, but a regression there fails silently: If-Match would be ignored
  and concurrent edits would overwrite each other without any error, which is the
  production bug (nginx gzip weakens ETags) this protection was built for.
"""

import json
from unittest.mock import MagicMock, patch

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from sqlalchemy.orm.exc import StaleDataError

from tests.utils import VerifyRecordPermissionPatch, get_json, postdata


@patch(
    "invenio_records_rest.views.verify_record_permission",
    MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_concurrent_delete_returns_409(client, org_martigny, item_type_data_tmp):
    """Concurrent DELETE must return 409.

    invenio-records-rest catches StaleDataError in its put() handler only: the
    delete() handler relies on the application error handler registered in ext.py
    to turn the conflict into a 409 instead of a 500. db.session.commit is patched
    to raise StaleDataError, the optimistic locking failure SQLAlchemy raises when
    two concurrent sessions try to commit the same record revision.
    """
    item_type_data_tmp["pid"] = "itty_concurrent"
    item_type_data_tmp["name"] = "concurrent delete"
    res, _ = postdata(client, "invenio_records_rest.itty_list", item_type_data_tmp)
    assert res.status_code == 201
    item_url = url_for("invenio_records_rest.itty_item", pid_value=item_type_data_tmp["pid"])

    with patch("invenio_db.db.session.commit", side_effect=StaleDataError()):
        res = client.delete(item_url)
        assert res.status_code == 409

    # The rolled back session stays usable: the record is still deletable
    assert client.delete(item_url).status_code == 204


def test_weak_etag_stale_revision_returns_412(client, librarian_martigny, patron_martigny, json_header):
    """PUT with a stale weak If-Match must be rejected with 412.

    nginx converts strong ETags ("N") to weak ETags (W/"N") when applying gzip
    compression (RFC 7232 §2.1). A weak If-Match matching the current revision
    must succeed, and once a first PUT advanced the revision, a second PUT
    carrying the original weak ETag must fail with 412: the precondition must be
    checked against the current revision, not silently bypassed.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    res = client.get(item_url)
    assert res.status_code == 200
    # Simulate nginx gzip: convert strong ETag "N" to weak W/"N"
    weak_etag = f"W/{res.headers['ETag']}"
    data = get_json(res)["metadata"]

    headers_with_weak_etag = [*json_header, ("If-Match", weak_etag)]

    # First PUT with the correct weak ETag — must succeed and advance the revision
    res = client.put(item_url, data=json.dumps(data), headers=headers_with_weak_etag)
    assert res.status_code == 200

    # Second PUT with the now-stale weak ETag — must be rejected
    res = client.put(item_url, data=json.dumps(data), headers=headers_with_weak_etag)
    assert res.status_code == 412
    assert res.get_json() == {
        "status": 412,
        "message": "The precondition on the request for the URL failed positive evaluation.",
    }
