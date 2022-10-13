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

"""Statistics Configuration Record tests."""

from __future__ import absolute_import, print_function

from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.stats_cfg.api import StatConfiguration
from rero_ils.modules.stats_cfg.api import stat_cfg_id_fetcher as fetcher


def test_stats_cfg_create(db, client, stats_cfg_martigny_data,
                          patron_martigny, librarian_martigny,
                          system_librarian_martigny):
    """Test statistics configuration creation."""
    login_user_via_session(client, system_librarian_martigny.user)
    stats_cfg = StatConfiguration.create(stats_cfg_martigny_data,
                                         delete_pid=True)
    assert stats_cfg == stats_cfg_martigny_data
    assert stats_cfg.get('pid') == '1'

    stats_cfg = StatConfiguration.get_record_by_pid('1')
    assert stats_cfg == stats_cfg_martigny_data

    fetched_pid = fetcher(stats_cfg.id, stats_cfg)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'stacfg'

    stats_cfg.delete()


def test_stats_cfg_can_delete(stats_cfg_martigny):
    """Test statistics configuration can delete."""

    assert stats_cfg_martigny.get_links_to_me('stats_cfg1') == {}

    can, reasons = stats_cfg_martigny.can_delete
    assert can
    assert reasons == {}
