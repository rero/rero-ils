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

"""Tests acquisition rollover process."""
import os
from copy import deepcopy

import mock
import pytest
from api.acquisition.acq_utils import _make_resource
from click.testing import CliRunner

from rero_ils.config import ROLLOVER_LOGGING_CONFIG
from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.acquisition.cli import rollover
from rero_ils.modules.acquisition.exceptions import (
    BudgetDoesNotExist,
    BudgetNotEmptyError,
    InactiveBudgetError,
    IncompatibleBudgetError,
)
from rero_ils.modules.acquisition.rollover import AcqRollover
from rero_ils.modules.utils import get_ref_for_pid


def test_rollover_cli(client, acq_full_structure_a, org_martigny):
    """Test rollover script using the CLI command."""

    origin_budget = acq_full_structure_a
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("logs")

        # Missing destination budget argument
        res = runner.invoke(rollover, [origin_budget.pid])
        assert res != 0
        # Missing parameters to create destination budget
        res = runner.invoke(rollover, [origin_budget.pid, "-n"])
        assert res != 0

        result = runner.invoke(
            rollover,
            [
                origin_budget.pid,
                "--new-budget",
                "--budget-name",
                "Budget destination",
                "--budget-start-date",
                "2022-01-01",
                "--budget-end-date",
                "2022-12-31",
            ],
        )
        assert result.exit_code == 0  # all works fine !


def test_rollover_exceptions(
    client, acq_full_structure_a, org_martigny, org_sion, lib_martigny
):
    """Test rollover process exceptions."""
    origin_budget = acq_full_structure_a
    # budget data
    ref_org_sion = get_ref_for_pid("org", org_sion.pid)
    ref_org_martigny = get_ref_for_pid("org", org_martigny.pid)

    destination_budget = {
        "name": "Budget destination",
        "start_date": "2022-01-01",
        "end_date": "2022-12-31",
        "is_active": False,
        "organisation": {"$ref": ref_org_martigny},
    }

    # Use special logging configuration to disable any logs
    logging_config = deepcopy(ROLLOVER_LOGGING_CONFIG)
    logging_config["handlers"]["console"] = {"class": "logging.NullHandler"}
    logging_config["handlers"]["file"] = {"class": "logging.NullHandler"}

    # TEST#1 :: Run rollover process without destination budget
    #    In this case, the rollover script will try to create a new budget
    #    using additional keyword arguments. If not present, it will raise
    #    AssertionError
    with pytest.raises(AssertionError) as err:
        AcqRollover(origin_budget, logging_config=logging_config)
    assert "param required" in str(err)

    # TEST#2 :: Rollover arguments validation
    #   * testing budget record existence.
    #   * testing budget in same organisation
    #   * testing original budget is active
    #   * testing destination budget is empty
    with pytest.raises(BudgetDoesNotExist):
        AcqRollover(
            origin_budget, {}, logging_config=logging_config, propagate_errors=True
        )

    destination_budget["organisation"]["$ref"] = ref_org_sion
    sion_budget = _make_resource(client, "budg", destination_budget)
    with pytest.raises(IncompatibleBudgetError):
        AcqRollover(
            origin_budget,
            sion_budget,
            logging_config=logging_config,
            propagate_errors=True,
        )

    destination_budget["organisation"]["$ref"] = ref_org_martigny
    dest_budget = _make_resource(client, "budg", destination_budget)
    origin_budget["is_active"] = False
    origin_budget.update(origin_budget, dbcommit=True, reindex=True)
    with pytest.raises(InactiveBudgetError):
        AcqRollover(
            origin_budget,
            dest_budget,
            logging_config=logging_config,
            propagate_errors=True,
        )

    origin_budget["is_active"] = True
    origin_budget.update(origin_budget, dbcommit=True, reindex=True)
    _make_resource(
        client,
        "acac",
        {
            "name": "account_1",
            "number": "000.0000.01",
            "allocated_amount": 1000,
            "budget": {"$ref": get_ref_for_pid("budg", dest_budget.pid)},
            "library": {"$ref": get_ref_for_pid("lib", lib_martigny.pid)},
        },
    )
    with pytest.raises(BudgetNotEmptyError):
        AcqRollover(
            origin_budget,
            dest_budget,
            logging_config=logging_config,
            propagate_errors=True,
        )


def test_rollover_misc_functions(client, acq_full_structure_a, org_martigny):
    """Test miscellaneous methods of rollover process.

    Test of these methods are difficult into a classic rollover process ; test
    them into this function to increase code coverage and ensure all works as
    expected.
    """
    original_budget = acq_full_structure_a
    destination_budget = _make_resource(
        client,
        "budg",
        {
            "name": "Budget destination",
            "start_date": "2022-01-01",
            "end_date": "2022-12-31",
            "is_active": False,
            "organisation": {"$ref": get_ref_for_pid("org", org_martigny.pid)},
        },
    )
    # Use special logging configuration to disable any logs
    logging_config = deepcopy(ROLLOVER_LOGGING_CONFIG)
    logging_config["handlers"]["console"] = {"class": "logging.NullHandler"}
    logging_config["handlers"]["file"] = {"class": "logging.NullHandler"}
    process = AcqRollover(
        original_budget, destination_budget, logging_config=logging_config
    )

    # TEST#1 :: budget creation by rollover process
    new_budget = process._create_new_budget(
        name="test_budget", start_date="2000-01-01", end_date="2000-12-31"
    )
    assert new_budget
    assert new_budget.name == "test_budget"

    # TEST#2 :: confirmation message
    with mock.patch("builtins.input", side_effect=["Y", "No", "inv", "y", ""]):
        confirmation = process._confirm('user will enter "Y"', default=None)
        assert confirmation
        confirmation = process._confirm('user will enter "n"')
        assert not confirmation
        confirmation = process._confirm('user will enter "inv", next "y"')
        assert confirmation
        confirmation = process._confirm("user just push ENTER", default="no")
        assert not confirmation

    with pytest.raises(ValueError):
        process._confirm("invalid default", default="dummy")

    # TEST#3 :: aborting ; this will delete the new created budget
    assert len(process._stack) == 1
    process._abort_rollover("dummy errors")
    control_budget = Budget.get_record_by_pid(new_budget.pid)
    assert not control_budget
