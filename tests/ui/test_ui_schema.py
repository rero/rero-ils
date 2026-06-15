# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CircPolicy Record tests."""

from invenio_jsonschemas import current_jsonschemas

from tests.utils import get_json


def test_get_schema(client, app):
    """Test schemas api in debug mode."""
    scheams_endpoint = app.config.get("JSONSCHEMAS_ENDPOINT")
    for schema in current_jsonschemas.list_schemas():
        # TODO: correct local://
        if "/" in schema and "record-v1.0.0.json" not in schema:
            url = f"{scheams_endpoint}/{schema}"
            res = client.get(url)
            assert res.status_code == 200
            data = get_json(res)
            if "properties" in data:
                assert data.get("$schema").startswith("http://json-schema.org/draft")
            # test resolved
            url = f"{url}?resolved=1"
            res = client.get(url)
            assert res.status_code == 200
            data = get_json(res)
            if "properties" in data:
                assert data.get("$schema").startswith("http://json-schema.org/draft")
