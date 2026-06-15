# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ILL requests record mapping tests."""

from rero_ils.modules.ill_requests.api import ILLRequest, ILLRequestsSearch
from tests.utils import get_mapping


def test_ill_request_search_mapping(es, db, loc_public_martigny, patron_martigny, ill_request_martigny_data):
    """Test ill request search index mapping."""
    search = ILLRequestsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    request = ILLRequest.create(ill_request_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    request.delete(force=True, dbcommit=True, delindex=True)
