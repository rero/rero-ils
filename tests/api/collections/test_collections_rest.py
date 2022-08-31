# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Tests REST API collections."""

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, flush_index, get_json

from rero_ils.modules.collections.api import CollectionsSearch


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_collections_facets(client, rero_json_header, coll_martigny_1):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.coll_list')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']
    # check all facets are present
    for facet in ['type', 'library', 'subject', 'teacher']:
        assert aggs[facet]

    # FILTERS
    # type
    list_url = url_for('invenio_records_rest.coll_list', type='course')
    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # library
    list_url = url_for('invenio_records_rest.coll_list', library='lib1')
    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # subject
    list_url = url_for('invenio_records_rest.coll_list', subject='geographic')
    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # teacher
    list_url = url_for(
        'invenio_records_rest.coll_list', teacher='Pr. Smith, John'
    )
    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_collection_enrich_data(client, document, item_type_standard_martigny,
                                item_lib_martigny, item2_lib_martigny,
                                loc_public_martigny, coll_martigny_1,
                                json_header):
    """Test record retrieval."""
    coll_martigny_1.reindex()
    flush_index(CollectionsSearch.Meta.index)
    query = CollectionsSearch()\
        .filter('term', pid=coll_martigny_1.pid)\
        .source().scan()
    coll_martigny_1_es_data = next(query)
    assert coll_martigny_1_es_data.organisation.pid == 'org1'
