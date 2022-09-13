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
from click import UsageError
from flask.cli import with_appcontext

from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.acquisition.exceptions import BudgetDoesNotExist
from rero_ils.modules.acquisition.rollover import AcqRollover
from rero_ils.modules.utils import get_ref_for_pid


@click.group()
def acquisition():
    """Acquisition management commands."""


@acquisition.command('rollover')
@click.argument('origin_budget_pid',
                type=str)
@click.option('-d', '--destination',
              'dest_budget_pid',
              type=str,
              help='Destination budget pid')
@click.option('-i', '--interactive',
              'interactive',
              is_flag=True,
              default=False,
              help='interactive mode')
@click.option('--new-budget',
              is_flag=True,
              default=False,
              help='Create a new destination budget resource')
@click.option('--budget-name',
              'budget_name',
              help='The new budget name')
@click.option('--budget-start-date',
              'budget_start_date',
              help='The new budget start-date')
@click.option('--budget-end-date',
              'budget_end_date',
              help='The new budget end-date')
@with_appcontext
def rollover(
    origin_budget_pid, dest_budget_pid,
    interactive,
    new_budget, budget_name, budget_start_date, budget_end_date
):
    """CLI to run rollover process between two acquisition budgets."""
    # Check parameters
    if not dest_budget_pid and not new_budget:
        raise UsageError('destination budget OR new budget is required')

    original_budget = Budget.get_record_by_pid(origin_budget_pid)
    # Try to create the destination budget if required
    if new_budget:
        if not all([budget_name, budget_start_date, budget_end_date]):
            raise UsageError('budget name, start-date, end-date are required')
        org_ref = get_ref_for_pid('org', original_budget.organisation_pid)
        data = {
            'organisation': {'$ref': org_ref},
            'is_active': False,
            'name': budget_name,
            'start_date': budget_start_date,
            'end_date': budget_end_date
        }
        destination_budget = Budget.create(data, dbcommit=True, reindex=True)
        if not destination_budget:
            raise BudgetDoesNotExist('Unable to create new budget')
        dest_budget_pid = destination_budget.pid

    destination_budget = Budget.get_record_by_pid(dest_budget_pid)
    rollover_runner = AcqRollover(
        original_budget, destination_budget, is_interactive=interactive)
    rollover_runner.run()
