# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

from flask import url_for
from utils import get_json


def test_holdings_pids(es_clear, client, holding_lib_sion, holding_lib_fully):
    """Test retrieve holdings pids by document pid."""
    url = url_for(
        'api_holding.holding_pids',
        document_pid=holding_lib_fully.document_pid,
        view='global'
    )
    res = client.get(url)
    assert res.status_code == 200

    data = get_json(res)
    assert len(data) == 2
    assert holding_lib_sion.get('pid') in data
    assert holding_lib_fully.get('pid') in data

    holding_lib_sion['_masked'] = True
    holding_lib_sion.update(holding_lib_sion, dbcommit=True, reindex=True)
    url = url_for(
        'api_holding.holding_pids',
        document_pid=holding_lib_sion.document_pid,
        view='global'
    )
    res = client.get(url)
    assert res.status_code == 200

    data = get_json(res)
    assert len(data) == 1

    url = url_for(
        'api_holding.holding_pids',
        document_pid=holding_lib_fully.document_pid,
        view='org1'
    )
    res = client.get(url)
    assert res.status_code == 200

    data = get_json(res)
    assert len(data) == 1
    assert holding_lib_fully.get('pid') in data

