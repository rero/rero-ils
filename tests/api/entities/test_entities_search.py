# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Search tests."""
import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_unified_entity_search(client, entity_person, local_entity_person,
                               entity_organisation):
    """Test unified entity search queries."""

    # unified entity search
    list_url = url_for(
        'invenio_records_rest.ent_list',
        q='"Loy, Georg"',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 2

    # unified entity search organisation
    list_url = url_for(
        'invenio_records_rest.ent_list',
        q='"Convegno internazionale di italianistica Craiova"',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # empty search
    list_url = url_for(
        'invenio_records_rest.ent_list',
        q='"Nebehay, Christian Michael"',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 0
