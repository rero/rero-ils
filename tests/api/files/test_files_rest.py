# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Tests files REST API."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json


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
