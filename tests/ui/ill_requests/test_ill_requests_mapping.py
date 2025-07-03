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

"""ILL requests record mapping tests."""

from rero_ils.modules.ill_requests.api import ILLRequest, ILLRequestsSearch
from tests.utils import get_mapping


def test_ill_request_es_mapping(
    es, db, loc_public_martigny, patron_martigny, ill_request_martigny_data
):
    """Test ill request elasticsearch mapping."""
    search = ILLRequestsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    request = ILLRequest.create(
        ill_request_martigny_data, dbcommit=True, reindex=True, delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
    request.delete(force=True, dbcommit=True, delindex=True)
