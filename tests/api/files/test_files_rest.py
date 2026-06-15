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
