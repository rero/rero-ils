# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Tests REST API items."""
from elasticsearch_dsl.search import Response
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from mock import mock
from utils import get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.operation_logs.api import OperationLogsSearch


def test_item_stats_endpoint(
    item_at_desk_martigny_patron_and_loan_at_desk,
    client, librarian_martigny
):
    """Test loan filter on stats endpoint with real data."""
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for(
        'api_item.stats',
        item_pid=item_at_desk_martigny_patron_and_loan_at_desk[0].pid
    ))
    assert res.json['total']['request'] == 1


def test_item_dumps(client, item_lib_martigny, org_martigny,
                    librarian_martigny):
    """Test item dumps and Elasticsearch version."""
    item_dumps = Item(item_lib_martigny.dumps()).replace_refs()

    assert item_dumps.get('organisation').get('pid') == org_martigny.pid

    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    item_es = Item(get_json(res).get('metadata'))
    assert item_es.is_available()
    assert item_es.organisation_pid == org_martigny.pid


def test_patron_checkouts_order(client, librarian_martigny,
                                patron_martigny, loc_public_martigny,
                                item_type_standard_martigny,
                                item3_lib_martigny, json_header,
                                item4_lib_martigny,
                                circulation_policies):
    """Test sort of checkout loans."""
    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item4_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    # sort by transaction_date asc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny.pid,
            sort='_created'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item3_lib_martigny.pid
    assert items[1]['item']['pid'] == item4_lib_martigny.pid

    # sort by transaction_date desc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny.pid,
            sort='-transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item4_lib_martigny.pid
    assert items[1]['item']['pid'] == item3_lib_martigny.pid

    # sort by invalid field
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny.pid,
            sort='does not exist'))
    assert res.status_code == 500
    data = get_json(res)
    assert 'RequestError(400' in data['status']


def test_item_stats(
    app, client, librarian_martigny, item_lib_martigny
):
    """Test item stats."""
    # A mock on the answer has been created, because it is not possible
    # to freeze on the date, because the string "now-1y" passed to
    # the configuration of the "year" facet is calculated
    # on the Elasticsearch instance.
    es_response = Response(OperationLogsSearch(), {
        'aggregations': {
            'trigger': {
                'buckets': [{
                    'doc_count': 1,
                    'key': 'checkout',
                    'year': {
                        'doc_count': 1,
                        'meta': {}
                    }
                }, {
                    'doc_count': 2,
                    'key': 'extend',
                    'year': {
                        'doc_count': 1,
                        'meta': {}
                    }
                }, {
                    'doc_count': 2,
                    'key': 'checkin',
                    'year': {
                        'doc_count': 1,
                        'meta': {}
                    }
                }]
            }
        }
    })

    es_response_checkin = Response(OperationLogsSearch(), {
        'aggregations': {
            'trigger': {
                'buckets': [{
                    'doc_count': 2,
                    'key': 'checkin',
                    'year': {
                        'doc_count': 1,
                        'meta': {}
                    }
                }]
            }
        }
    })

    login_user_via_session(client, librarian_martigny.user)
    with mock.patch.object(
        OperationLogsSearch,
        'execute',
        mock.MagicMock(return_value=es_response)
    ):
        # We sum the Legacy_count field in the checkout field
        res = client.get(url_for('api_item.stats', item_pid='item1'))
        assert res.json == \
            {
                'total': {'checkout': 5, 'extend': 2, 'checkin': 2},
                'total_year': {'checkout': 1, 'extend': 1, 'checkin': 1}}

    with mock.patch.object(
        OperationLogsSearch,
        'execute',
        mock.MagicMock(return_value=es_response_checkin)
    ):
        # item found
        # We add the legacy_checkout_count field to the checkout field
        res = client.get(url_for('api_item.stats', item_pid='item1'))
        assert res.json == \
            {
                'total': {'checkout': 4, 'checkin': 2},
                'total_year': {'checkin': 1}}
        # No item found
        res = client.get(url_for('api_item.stats', item_pid='foot'))
        assert res.json == \
            {
                'total': {'checkin': 2},
                'total_year': {'checkin': 1}}
