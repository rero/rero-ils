# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Click command-line utilities about acquisition."""

import click
from flask.cli import with_appcontext

from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.acquisition.rollover import AcqRollover


@click.group()
def acquisition():
    """Acquisition management commands."""


@acquisition.command('rollover')
@click.option('-o', '--origin', 'origin_budget_pid',
              required=True, type=str, help='Origin budget pid')
@click.option('-d', '--destination', 'dest_budget_pid',
              required=True, type=str, help='Destination budget pid')
@click.option('-i', '--interactive', 'interactive', is_flag=True,
              show_default=True, default=False, help='interactive mode')
@with_appcontext
def rollover(origin_budget_pid, dest_budget_pid, interactive):
    """CLI to run rollover process between two acquisition budgets."""
    original_budget = Budget.get_record_by_pid(origin_budget_pid)
    destination_budget = Budget.get_record_by_pid(dest_budget_pid)
    rollover_runner = AcqRollover(
        original_budget, destination_budget, is_interactive=interactive)
    rollover_runner.run()
