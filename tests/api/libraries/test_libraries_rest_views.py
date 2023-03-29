# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Tests REST API libraries."""

from flask import url_for
from utils import get_json, login_user


def test_library_closed_date_api(client, lib_martigny, librarian_martigny):
    """Test closed date api."""
    login_user(client, librarian_martigny)
    # CHECK#0 :: unknown library
    url = url_for(
        'api_library.list_closed_dates',
        library_pid='dummy_pid'
    )
    res = client.get(url)
    assert res.status_code == 404

    # CHECK#1 :: no specified dates
    url = url_for(
        'api_library.list_closed_dates',
        library_pid=lib_martigny.pid
    )
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert 'closed_dates' in data
    assert isinstance(data['closed_dates'], list)

    # CHECK#2 :: with specified dates
    params = {
        'from': '2020-01-01',
        'until': '2020-02-01'
    }
    url = url_for(
        'api_library.list_closed_dates',
        library_pid=lib_martigny.pid,
        **params
    )
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['params']['from'] == params['from']
    assert data['params']['until'] == params['until']

    # CHECK#3 :: with bad specified dates
    params = {
        'until': '2020-01-01',
        'from': '2020-02-01'
    }
    url = url_for(
        'api_library.list_closed_dates',
        library_pid=lib_martigny.pid,
        **params
    )
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['params']['from'] == params['from']
    assert data['params']['until'] == params['until']
    assert data['closed_dates'] == []
