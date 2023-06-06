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

"""Entities Record utils."""
import pytest
from mock import mock
from requests import RequestException
from utils import mock_response

from rero_ils.modules.entities.remote_entities.utils import \
    get_mef_data_by_type


@mock.patch('requests.Session.get')
def test_utils_mef_data(mock_get, app):
    """."""
    with pytest.raises(KeyError):
        get_mef_data_by_type('idref', 'pid', 'dummy_entity', verbose=True)

    mock_get.return_value = mock_response(
        json_data={'hits': {'hits': [], 'toto': 'foo'}})
    with pytest.raises(ValueError):
        get_mef_data_by_type('viaf', 'pid', 'agents', verbose=True)

    mock_get.return_value = mock_response(
        status=400, json_data={'error': 'Bad request'})
    with pytest.raises(RequestException):
        get_mef_data_by_type('viaf', 'pid', 'agents', verbose=True)
