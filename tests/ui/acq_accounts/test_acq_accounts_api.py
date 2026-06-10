# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition account API tests."""

from rero_ils.modules.acquisition.acq_accounts.models import AcqAccountExceedanceType


def test_get_exceedance(acq_account_fiction_martigny):
    """Test get_exceedance returns the correct percentage of the allocated amount."""
    acac = acq_account_fiction_martigny
    assert acac["allocated_amount"] == 15000

    # No exceedance configured → 0 for both types
    assert acac.get_exceedance(AcqAccountExceedanceType.ENCUMBRANCE) == 0
    assert acac.get_exceedance(AcqAccountExceedanceType.EXPENDITURE) == 0

    # 5% of 15000.00 = 750.0
    acac["encumbrance_exceedance"] = 5
    assert acac.get_exceedance(AcqAccountExceedanceType.ENCUMBRANCE) == 750.0
    assert acac.get_exceedance(AcqAccountExceedanceType.EXPENDITURE) == 0

    # 10% of 15000.00 = 1500.0
    acac["expenditure_exceedance"] = 10
    assert acac.get_exceedance(AcqAccountExceedanceType.EXPENDITURE) == 1500.0

    # Fractional rate: 1.5% of 15000.00 = 225.0
    acac["encumbrance_exceedance"] = 1.5
    assert acac.get_exceedance(AcqAccountExceedanceType.ENCUMBRANCE) == 225.0

    # Float precision: 7% of 1000.10 = 70.007 → rounds to 70.01
    # Without round(,2) this would return 70.007 or drift further
    acac["allocated_amount"] = 1000.10
    acac["encumbrance_exceedance"] = 7
    assert acac.get_exceedance(AcqAccountExceedanceType.ENCUMBRANCE) == 70.01

    del acac["encumbrance_exceedance"]
    del acac["expenditure_exceedance"]
