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

"""DOJSON transformation for Dublin Core module tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import mock
from utils import mock_response

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.documents.tasks import find_contribution


@mock.patch('requests.get')
def test_find_contribution(mock_contributions_mef_get, app, document_data,
                           contribution_person_response_data):
    """Test find contribution."""

    assert find_contribution() == (0, 0, 0, 0)

    doc = Document.create(data=document_data, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()
    assert find_contribution() == (0, 0, 0, 1)

    without_idref = deepcopy(contribution_person_response_data)
    without_idref['hits']['hits'][0]['metadata'].pop('idref')
    mock_contributions_mef_get.return_value = mock_response(
        json_data=without_idref
    )
    assert find_contribution() == (0, 0, 1, 0)

    mock_contributions_mef_get.return_value = mock_response(
        json_data=contribution_person_response_data
    )
    assert find_contribution() == (1, 0, 0, 0)
