# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Loans Record dumper tests."""

from rero_ils.modules.loans.dumpers import CirculationDumper


def test_loan_circulation_dumper(loan_pending_martigny):
    """Test loan circulation action dumper."""
    data = loan_pending_martigny.dumps(CirculationDumper())
    assert data["state"]
    assert data["creation_date"]
    assert "name" in data["patron"]
    assert "barcode" in data["patron"]
    assert "name" in data["pickup_location"]
    assert "library_name" in data["pickup_location"]
