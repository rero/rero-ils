# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for concurrent record update protection via ETag / If-Match.

These tests verify observable HTTP behaviour (status codes, response bodies) and
pass regardless of whether the protection is implemented via workarounds in
ext.py or via upstream fixes in invenio-records-rest / invenio-rest.
"""

import json
from unittest.mock import patch

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from sqlalchemy.orm.exc import StaleDataError

from tests.utils import get_json


def test_concurrent_put_through_records_rest_returns_409(client, librarian_martigny, patron_martigny, json_header):
    """Concurrent PUT through invenio-records-rest must return 409.

    Patches db.session.commit to raise StaleDataError, simulating the optimistic
    locking failure that SQLAlchemy raises when two concurrent sessions try to
    commit the same record revision. This exercises the full invenio-records-rest
    PUT code path and verifies that the 409 response is produced.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)["metadata"]

    with patch("invenio_db.db.session.commit", side_effect=StaleDataError()):
        res = client.put(item_url, data=json.dumps(data), headers=json_header)
        assert res.status_code == 409
        assert res.get_json() == {
            "status": 409,
            "message": "A conflict happened while processing the request. The resource might have been modified while the request was being processed.",
        }


def test_sequential_updates_without_etag_succeed(client, librarian_martigny, patron_martigny, json_header):
    """Sequential PUTs without If-Match must both succeed.

    Without concurrent requests there is no version conflict, so two
    sequential PUTs without If-Match must each return 200 and advance
    the ETag independently.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    res = client.get(item_url)
    assert res.status_code == 200
    etag = res.headers["ETag"]
    data = get_json(res)["metadata"]

    # First PUT — must succeed and advance the revision
    res = client.put(item_url, data=json.dumps(data), headers=json_header)
    assert res.status_code == 200
    assert res.headers["ETag"] != etag

    # Second PUT — must also succeed (sequential, no real concurrency)
    etag = res.headers["ETag"]
    res = client.put(item_url, data=json.dumps(data), headers=json_header)
    assert res.status_code == 200
    assert res.headers["ETag"] != etag


def test_weak_etag_matching_current_revision_succeeds(client, librarian_martigny, patron_martigny, json_header):
    """PUT with a weak If-Match matching the current revision must succeed.

    nginx converts strong ETags ("N") to weak ETags (W/"N") when applying gzip
    compression (RFC 7232 §2.1). The server must accept weak ETags in If-Match
    and succeed when the version matches.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    res = client.get(item_url)
    assert res.status_code == 200
    # Simulate nginx gzip: convert strong ETag "N" to weak W/"N"
    weak_etag = f"W/{res.headers['ETag']}"
    data = get_json(res)["metadata"]

    res = client.put(item_url, data=json.dumps(data), headers=[*json_header, ("If-Match", weak_etag)])
    assert res.status_code == 200


def test_weak_etag_stale_revision_returns_412(client, librarian_martigny, patron_martigny, json_header):
    """PUT with a stale weak If-Match must be rejected with 412.

    After a first PUT advances the revision, a second PUT carrying the original
    weak ETag (W/"N") must fail with 412 — the server must check weak ETags
    in If-Match against the current revision, not silently bypass the check.
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


def test_etag_prevents_stale_concurrent_update(client, librarian_martigny, patron_martigny, json_header):
    """Second PUT with a stale ETag must be rejected with 412.

    Simulates a double-click or two concurrent saves by sending two PUT
    requests carrying the same If-Match value. After the first PUT commits,
    the record revision advances and the second PUT must fail with 412
    Precondition Failed rather than silently overwriting or returning 500.
    """
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid)

    # Capture the current ETag from a GET
    res = client.get(item_url)
    assert res.status_code == 200
    etag = res.headers["ETag"]
    data = get_json(res)["metadata"]

    headers_with_etag = [*json_header, ("If-Match", etag)]

    # First PUT with the correct ETag — must succeed and advance the revision
    res = client.put(item_url, data=json.dumps(data), headers=headers_with_etag)
    assert res.status_code == 200
    assert res.headers["ETag"] != etag

    # Second PUT with the now-stale ETag — must be rejected
    res = client.put(item_url, data=json.dumps(data), headers=headers_with_etag)
    assert res.status_code == 412
    assert res.get_json() == {
        "status": 412,
        "message": "The precondition on the request for the URL failed positive evaluation.",
    }
