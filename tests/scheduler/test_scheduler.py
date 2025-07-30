# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Tests scheduler."""

from click.testing import CliRunner

from rero_ils.schedulers import (
    current_scheduler,
    enable_tasks,
    info,
    init,
)


def test_scheduler(celery_session):
    """Test scheduler."""
    display_tasks = [
        (
            "- bulk-indexer = rero_ils.modules.tasks.process_bulk_queue | "
            "<freq: 1.00 hour> | "
            "kwargs:{} | "
            # "options:{} "
            "enabled:False"
        )
    ]
    current_scheduler.reset()
    current_scheduler.setup_schedule()
    assert current_scheduler.display_all() == display_tasks

    entry = current_scheduler.get("bulk-indexer")
    assert not current_scheduler.is_due(entry).is_due

    current_scheduler.set_entry_enabled("bulk-indexer", True)
    enabled_task = display_tasks[0].replace("enabled:False", "enabled:True")
    assert current_scheduler.display_all() == [enabled_task]

    entry = current_scheduler.get("bulk-indexer")
    # TODO: not always working ???
    # assert not current_scheduler.is_due(entry).is_due


def test_scheduler_cli(celery_session):
    """Test scheduler cli."""
    display_tasks = [
        (
            "- bulk-indexer = rero_ils.modules.tasks.process_bulk_queue | "
            "<freq: 1.00 hour> | "
            "kwargs:{} | "
            # "options:{} "
            "enabled:False"
        )
    ]
    runner = CliRunner()
    res = runner.invoke(init, ["-r", "-v"])
    assert res.output.strip().split("\n") == [
        "Reset DB scheduler!",
        display_tasks[0],
    ]

    res = runner.invoke(init, ["-v"])
    assert res.output.strip().split("\n") == [
        "Initalize DB scheduler!",
        display_tasks[0],
    ]

    res = runner.invoke(enable_tasks, ["-a", "-v"])
    enabled_task = display_tasks[0].replace("enabled:False", "enabled:True")
    assert res.output.strip().split("\n") == ["Scheduler tasks enabled:", enabled_task]

    res = runner.invoke(enable_tasks, ["-v", "-n bulk-indexer", "-n dummy", "-d"])
    assert res.output.strip().split("\n") == [
        "Scheduler tasks enabled:",
        display_tasks[0],
        "Not found entry: dummy",
    ]

    res = runner.invoke(info, [])
    assert res.output.strip().split("\n") == ["Scheduled tasks:", display_tasks[0]]
