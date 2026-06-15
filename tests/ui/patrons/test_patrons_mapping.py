# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron search index mapping tests."""

from rero_ils.modules.patrons.api import PatronsSearch
from tests.utils import get_mapping


def test_patron_mapping(roles, search, lib_martigny, librarian_martigny_data_tmp):
    """Test patron search index mapping."""
    search = PatronsSearch()
    mapping = get_mapping(search.Meta.index)
    # TODO: create of an patron
    assert mapping == get_mapping(search.Meta.index)


def test_patron_search_mapping(app, patrons_records, librarian_saxon):
    """Test patron search mapping."""
    search = PatronsSearch()

    assert search.query("query_string", query="Roduit").count() == 1
    assert search.query("match", first_name="Eric").count() == 1
    assert search.query("match", last_name="Moret").count() == 1
    assert search.query("match", first_name="Elena").count() == 1

    eq_query = search.query("match", first_name="Eléna").source(["pid"]).scan()
    pids = [hit.pid for hit in eq_query]
    assert len(pids) == 1
    assert librarian_saxon.pid in pids
