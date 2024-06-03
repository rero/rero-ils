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

from celery import current_app as current_celery
from click.testing import CliRunner

from rero_ils.schedulers import (
    RedisScheduler,
    current_scheduler,
    enable_tasks,
    info,
    init,
)


def test_scheduler(app):
    """Test scheduler."""
    display_tasks = [
        (
            "- bulk-indexer = rero_ils.modules.tasks.process_bulk_queue "
            "<freq: 1.00 hour> "
            "kwargs:{} "
            "options:{} "
            "enabled:False"
        )
    ]
    # clean the REDIS DB
    current_scheduler._remove_db()
    # create the scheduled test tasks
    RedisScheduler(app=current_celery)
    assert current_scheduler.display_all() == display_tasks
    assert not current_scheduler.get_entry_enabled("bulk-indexer")

    entry = current_scheduler.get("bulk-indexer")
    assert not current_scheduler.is_due(entry).is_due

    current_scheduler.set_entry_enabled("bulk-indexer", True)
    assert current_scheduler.get_entry_enabled("bulk-indexer")
    enabled_task = display_tasks[0].replace("enabled:False", "enabled:True")
    assert current_scheduler.display_all() == [enabled_task]

    entry = current_scheduler.get("bulk-indexer")
    assert not current_scheduler.is_due(entry).is_due
    current_scheduler.remove("bulk-indexer")
    assert current_scheduler.display_all() == []

    assert current_scheduler.add_entry(entry, enable=False)
    assert current_scheduler.display_all() == display_tasks

    entry.kwargs["test"] = "test"
    current_scheduler.set(entry, enable=False)
    test_task = display_tasks[0].replace("kwargs:{}", "kwargs:{'test': 'test'}")
    assert current_scheduler.display_all() == [test_task]


def test_scheduler_cli(app):
    """Test scheduler cli."""
    display_tasks = [
        (
            "- bulk-indexer = rero_ils.modules.tasks.process_bulk_queue "
            "<freq: 1.00 hour> "
            "kwargs:{} "
            "options:{} "
            "enabled:False"
        )
    ]
    runner = CliRunner()
    res = runner.invoke(init, ["-r", "-v"])
    assert res.output.strip().split("\n") == [
        "Reset REDIS scheduler!",
        display_tasks[0],
    ]

    res = runner.invoke(init, ["-v"])
    assert res.output.strip().split("\n") == [
        "Initalize REDIS scheduler!",
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
