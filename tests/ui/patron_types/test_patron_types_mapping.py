# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron type search index mapping tests."""

from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch
from tests.utils import get_mapping


def test_patron_type_search_mapping(org_martigny, patron_type_children_martigny_data):
    """Test patron types es mapping."""
    search = PatronTypesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    PatronType.create(
        patron_type_children_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    assert mapping == get_mapping(search.Meta.index)


def test_patron_types_search_mapping(app, patron_types_records):
    """Test patron type search mapping."""
    search = PatronTypesSearch()

    c = search.query("query_string", query="patrons").count()
    # there is one more result from test_patron_type_search_mapping function
    assert c == 4

    c = search.query("match", name="patrons").count()
    assert c == 0

    c = search.query("match", name="children").count()
    # there is one more result from test_patron_type_search_mapping function
    assert c == 1

    pids = [r.pid for r in search.query("match", name="children").source(["pid"]).scan()]
    assert "ptty1" in pids
