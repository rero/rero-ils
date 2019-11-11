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

"""MEF persons utilities tests."""

from __future__ import absolute_import, print_function

import mock
import pytest
from utils import mock_response
from rero_ils.modules.mef_persons.utils import resolve_mef


@mock.patch('rero_ils.modules.mef_persons.utils.requests_get')
def test_mef_person_resolver(mock_resolver_get,
                             mef_person_response_data,
                             app,
                             document_ref,
                             mef_person):
    """test MEF reference resolver."""
    mock_resolver_get.return_value = mock_response(
        json_data=mef_person_response_data
    )

    mef_uri = document_ref.get('authors')[0].get('$ref')
    data = resolve_mef(mef_uri)

    assert mef_person.pid == data['id']
