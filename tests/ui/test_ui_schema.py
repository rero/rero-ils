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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from invenio_jsonschemas import current_jsonschemas
from utils import get_json


def test_get_schema(client, app):
    """Test schemas api in debug mode."""
    scheams_endpoint = app.config.get('JSONSCHEMAS_ENDPOINT')
    for schema in current_jsonschemas.list_schemas():
        # TODO: correct local://
        if '/' in schema and 'record-v1.0.0.json' not in schema:
            url = f'{scheams_endpoint}/{schema}'
            res = client.get(url)
            assert res.status_code == 200
            data = get_json(res)
            if 'properties' in data:
                assert data.get(
                    '$schema').startswith('http://json-schema.org/draft')
            # test resolved
            url = f'{url}?resolved=1'
            res = client.get(url)
            assert res.status_code == 200
            data = get_json(res)
            if 'properties' in data:
                assert data.get(
                    '$schema').startswith('http://json-schema.org/draft')
