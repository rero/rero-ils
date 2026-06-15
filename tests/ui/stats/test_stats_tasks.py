# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stats Report tests celery tasks."""

from rero_ils.modules.stats.tasks import collect_stats_reports


def test_stats_task_report(stats_cfg_martigny):
    """Test stat task reports generation."""
    res = collect_stats_reports("year")
    assert not res

    res = collect_stats_reports("month")
    assert len(res) > 0
