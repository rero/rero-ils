# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics Configuration search index mapping tests."""

from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.stats_cfg.api import StatConfiguration, StatsConfigurationSearch
from tests.utils import get_mapping


def test_stats_cfg_mapping(client, stats_cfg_martigny_data, system_librarian_martigny):
    """Test statistics configuration search index mapping."""
    search = StatsConfigurationSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping

    login_user_via_session(client, system_librarian_martigny.user)
    stats_cfg = StatConfiguration.create(stats_cfg_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    stats_cfg.delete(force=True, dbcommit=True, delindex=True)


def test_stats_cfg_search_mapping(app, stats_cfg_martigny, stats_cfg_sion):
    """Test statistics configuration search mapping."""
    search = StatsConfigurationSearch()

    search_query = search.source(["pid"]).scan()
    pids = [hit.pid for hit in search_query]
    assert len(pids) == 2
    assert "stats_cfg2" in pids
