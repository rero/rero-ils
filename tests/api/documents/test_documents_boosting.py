# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests boosting query for documents."""

from flask import url_for

from tests.utils import get_json


def test_document_boosting(client, roles, ebook_1, ebook_4):
    """Test document boosting."""
    list_url = url_for("invenio_records_rest.doc_list", q="maison")
    res = client.get(list_url)

    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 2
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == ebook_1.pid

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q="autocomplete_title:maison AND contribution.entity.authorized_access_point_en:James",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == ebook_1.pid
