# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries search index mapping tests."""

from rero_ils.modules.local_fields.api import LocalField, LocalFieldsSearch
from tests.utils import get_mapping


def test_local_field_search_mapping(es, db, org_martigny, document, local_field_martigny_data):
    """Test local field search index mapping."""
    search = LocalFieldsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    lf = LocalField.create(local_field_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    lf.delete(force=True, dbcommit=True, delindex=True)


def test_libraries_search_mapping(app, org_martigny, org_sion, document, local_fields_records):
    """Test local field search mapping."""
    search = LocalFieldsSearch()

    assert search.query("query_string", query="Auteur").count() == 2
    assert search.query("query_string", query="Bibliographie").count() == 1

    pids = [r.pid for r in search.query("match", fields__field_2="students").source(["pid"]).scan()]
    assert "lofi2" in pids
