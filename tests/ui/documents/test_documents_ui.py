# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests UI view for documents."""

from flask import url_for


def test_documents_detailed_view(client, loc_public_martigny, document):
    """Test document detailed view."""
    # check redirection
    res = client.get(url_for("invenio_records_ui.doc", viewcode="global", pid_value="doc1"))
    assert res.status_code == 200


def tests_document_item_filter_detailed_view(client, loc_public_martigny, document):
    """Test document detailed view with items filter."""
    res = client.get(url_for("invenio_records_ui.doc", viewcode="org1", pid_value="doc1"))
    assert res.status_code == 200


def tests_document_export_formats(client, document):
    """Test document export view format."""
    for _format in ["json", "ris"]:
        res = client.get(
            url_for(
                "invenio_records_ui.doc_export",
                viewcode="global",
                pid_value=document.pid,
                format=_format,
            )
        )
        assert res.status_code == 200
