# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Search tests."""

from unittest import mock

from flask import url_for

from tests.utils import VerifyRecordPermissionPatch, get_json


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_unified_entity_search(client, entity_person, local_entity_person, entity_organisation):
    """Test unified entity search queries."""

    # unified entity search
    list_url = url_for("invenio_records_rest.ent_list", q='"Loy, Georg"', simple="1")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 2

    # unified entity search organisation
    list_url = url_for(
        "invenio_records_rest.ent_list",
        q='"Convegno internazionale di italianistica Craiova"',
        simple="1",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1

    # empty search
    list_url = url_for("invenio_records_rest.ent_list", q='"Nebehay, Christian Michael"', simple="1")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 0
