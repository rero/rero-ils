# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries search index mapping tests."""

from rero_ils.modules.libraries.api import LibrariesSearch, Library
from tests.utils import get_mapping


def test_library_search_mapping(search, db, lib_martigny_data, org_martigny):
    """Test library search index mapping."""
    search = LibrariesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    lib = Library.create(lib_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    lib.delete(force=True, dbcommit=True, delindex=True)


def test_libraries_search_mapping(app, libraries_records):
    """Test library search mapping."""
    search = LibrariesSearch()

    assert search.query("query_string", query="Fully Library Restricted Space").count() == 4
    assert search.query("query_string", query="bibliothèque").count() == 1
    assert search.query("query_string", query="library AND Martigny").count() == 1
    assert search.query("match", name="Aproz").count() == 1

    search_query = search.query("match", name="Sion").source(["pid"]).scan()
    pids = [hit.pid for hit in search_query]
    assert len(pids) == 1
    assert "lib4" in pids
