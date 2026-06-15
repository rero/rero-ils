# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Serializers."""

from unittest import mock

from flask import url_for

from tests.utils import VerifyRecordPermissionPatch, get_json


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_json_export_serializers(client, export_json_header, document, export_document):
    """Test JSON export serializers for documents."""
    item_url = url_for("invenio_records_rest.doc_item", pid_value=export_document.pid)
    response = client.get(item_url, headers=export_json_header)
    assert response.status_code == 200
    # Get the first result.
    data = get_json(response)
    # Check if all desired keys not in data
    for key in ["created", "updated", "id", "links", "metadata"]:
        assert key not in data

    list_url = url_for("invenio_records_rest.doc_list", q=f"pid:{export_document.pid}")
    response = client.get(list_url, headers=export_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for key in ["created", "updated", "id", "links", "metadata"]:
        assert key not in data


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_ris_serializer(client, ris_header, document, export_document):
    """Test RIS formatter"""
    ris_tag = [
        "TY  -",
        "ID  -",
        "TI  -",
        "T2  -",
        "AU  -",
        "A2  -",
        "DA  -",
        "SP  -",
        "EP  -",
        "CY  -",
        "LA  -",
        "PB  -",
        "SN  -",
        "UR  -",
        "KW  -",
        "ET  -",
        "DO  -",
        "VL  -",
        "IS  -",
        "PP  -",
        "Y1  -",
        "PY  -",
        "ER  -",
    ]
    list_url = url_for("invenio_records_rest.doc_list", q=f"pid:{export_document.pid}")
    response = client.get(list_url, headers=ris_header)
    assert response.status_code == 200
    ris_data = response.get_data(as_text=True)
    assert all(tag in ris_data for tag in ris_tag)
    ris_list_tags = ["A1  -", "A2  -", "A3  -", "A4  -", "AU  -", "KW  -", "N1  -", "UR  -"]
    # check that there is only one of each RIS tag that is not repeatable
    for tag in ris_tag:
        if tag not in ris_list_tags:
            assert ris_data.count(tag) == 1
