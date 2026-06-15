# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests UI view for documents."""

from flask import url_for


def test_file_preview(client, document_with_files):
    """Test document detailed view."""
    record_file = next(document_with_files.get_records_files())
    files = [f for f in record_file.files if f.endswith((".pdf", ".png"))]
    res = client.get(url_for("invenio_records_ui.recid_preview", pid_value="foo", filename="foo.pdf"))

    assert res.status_code == 404

    res = client.get(
        url_for(
            "invenio_records_ui.recid_preview",
            pid_value=record_file["id"],
            filename="foo.pdf",
        )
    )
    assert res.status_code == 404

    for fname in files:
        res = client.get(
            url_for(
                "invenio_records_ui.recid_preview",
                pid_value=record_file["id"],
                filename=fname,
            )
        )
        assert res.status_code == 200
