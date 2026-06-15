# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patrons record dumper tests."""

from rero_ils.modules.patrons.dumpers import PatronPropertiesDumper


def test_patron_properties_dumper(patron_martigny):
    """Test patron properties dumper."""
    dumper = PatronPropertiesDumper(["formatted_name", "dummy"])
    dumped_data = patron_martigny.dumps(dumper=dumper)
    assert "formatted_name" in dumped_data
    assert "dummy" not in dumped_data
