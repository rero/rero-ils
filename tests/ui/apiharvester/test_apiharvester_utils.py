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

"""Api harvester tests."""

from __future__ import absolute_import, print_function

import mock
from utils import mock_response

from rero_ils.modules.apiharvester.tasks import harvest_records
from rero_ils.modules.apiharvester.utils import api_source, get_records


@mock.patch('requests.get')
def test_api_source(mock_get, app, capsys):
    """Test api source creation update."""
    msg = api_source(name='test', url='http://test.com')
    assert msg == 'Added'

    mock_get.return_value = mock_response(json_data={
        'hits': {
            'hits': [
                {'metadata': {'pid': 'test1', 'data': 'test data 1'}},
                {'metadata': {'pid': 'test2', 'data': 'test data 2'}}
            ],
            'total': {
                'value': 2
            },
            'links': {
                'self': 'http:/test.com'
            }
        }
    })
    harvest_records(name='test', url='http://test.com', signals=False,
                    size=1000, max_results=1000)
    out, err = capsys.readouterr()
    assert out.strip() == 'API records found: 2'

    msg = api_source(name='test', url='http://test.com', size=1000)
    assert msg == 'Not Updated'
    msg = api_source(name='test', url='http://test.com', mimetype='mimetype',
                     size=1000, comment='comment', update=True)
    assert msg == ('Updated: url:http://test.com, mimetype:mimetype,'
                   ' size:1000, comment:comment')


@mock.patch('requests.get')
def test_get_records(mock_get, app, capsys):
    """Test finding a circulation policy."""
    mock_get.return_value = mock_response(json_data={
        'hits': {
            'hits': [
                {'metadata': {'pid': 'test1', 'data': 'test data 1'}},
                {'metadata': {'pid': 'test2', 'data': 'test data 2'}}
            ],
            'total': {
                'value': 2
            },
            'links': {
                'self': 'http:/test.com'
            }
        }
    })
    for next_url, data in get_records(url='http://test.com', name='test',
                                      signals=False):
        assert next_url
        assert data == [
            {'data': 'test data 1', 'pid': 'test1'},
            {'data': 'test data 2', 'pid': 'test2'}
        ]
    out, err = capsys.readouterr()
    assert out.strip() == 'API records found: 2'
    mock_get.return_value = mock_response(json_data={
        'hits': {
            'hits': [
                {'metadata': {'pid': 'test3', 'data': 'test data 3'}},
                {'metadata': {'pid': 'test4', 'data': 'test data 4'}}
            ],
            'total': {
                'value': 2
            },
            'links': {
                'self': 'http:/test.com'
            }
        }
    })
    for next_url, data in get_records(url='http://test.com', name='test',
                                      from_date='1970-01-01', signals=False):
        assert next_url
        assert data == [
            {'data': 'test data 3', 'pid': 'test3'},
            {'data': 'test data 4', 'pid': 'test4'}
        ]
    out, err = capsys.readouterr()
    assert out.strip() == 'API records found: 2'
