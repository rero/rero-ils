# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation Policy Record tests."""

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy
from tests.utils import get_mapping


def test_circ_policy_search_mapping(search_clear, db, org_martigny, circ_policy_martigny_data_tmp):
    """Test circulation policy search index mapping."""
    search = CircPoliciesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    CircPolicy.create(circ_policy_martigny_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)


def test_circ_policies_search_mapping(app, circulation_policies):
    """Test circulation policy search mapping."""
    search = CircPoliciesSearch()

    c = search.query("query_string", query="policy").count()
    assert c == 4
    c = search.query("match", name="default").count()
    assert c == 2
    search_query = search.query("match", name="temporary").source(["pid"]).scan()
    pids = [hit.pid for hit in search_query]
    assert len(pids) == 1
    assert "cipo3" in pids
