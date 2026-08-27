# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests files REST API."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import get_json


def test_documents_get(client, document_with_files, librarian_martigny):
    """Test file record retrieval."""
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for("records.search")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    metadata = data["hits"]["hits"][0]
    assert set(metadata["metadata"]) == {
        "collections",
        "document",
        "library",
        "n_files",
        "file_size",
    }


def test_files_get(client, document_with_files, librarian_martigny):
    """Test the file list of a record.

    Only the extracted full texts and the thumbnails carry a type, so the
    uploaded files are the ones left in the list.
    """
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for("records.search"))
    assert res.status_code == 200
    record_id = get_json(res)["hits"]["hits"][0]["id"]

    res = client.get(url_for("records_files.search", pid_value=record_id))
    assert res.status_code == 200

    entries = get_json(res)["entries"]
    assert entries
    # the uploaded files are listed, the derivatives are filtered out
    assert all(entry.get("metadata", {}).get("type") is None for entry in entries)
    assert any(entry["key"].endswith(".pdf") for entry in entries)


def test_files_have_metadata(document_with_files):
    """Test that a committed file ends up with a metadata entry.

    The entry is written by the `extract_file_metadata` task, which runs under the system identity once the
    file is committed. The task logs its own errors instead of raising, so a missing permission leaves every
    file without metadata without anything failing.
    """
    record_file = next(document_with_files.get_records_files())
    assert record_file.files
    for key, file_record in record_file.files.items():
        assert file_record.metadata is not None, f"{key} has no metadata entry"
