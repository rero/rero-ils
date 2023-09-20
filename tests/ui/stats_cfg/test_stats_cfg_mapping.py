# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Statistics Configuration elasticsearch mapping tests."""

from invenio_accounts.testutils import login_user_via_session
from utils import get_mapping

from rero_ils.modules.stats_cfg.api import StatConfiguration, \
    StatsConfigurationSearch


def test_stats_cfg_es_mapping(client, stats_cfg_martigny_data,
                              system_librarian_martigny):
    """Test statistics configuration elasticsearch mapping."""
    search = StatsConfigurationSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping

    login_user_via_session(client, system_librarian_martigny.user)
    stats_cfg = StatConfiguration.create(
        stats_cfg_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    stats_cfg.delete(force=True, dbcommit=True, delindex=True)


def test_stats_cfg_search_mapping(app, stats_cfg_martigny, stats_cfg_sion):
    """Test statistics configuration search mapping."""
    search = StatsConfigurationSearch()

    es_query = search.source(['pid']).scan()
    pids = [hit.pid for hit in es_query]
    assert len(pids) == 2
    assert 'stats_cfg2' in pids
