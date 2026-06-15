# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation policies tests."""

from rero_ils.modules.circ_policies.api import CircPolicy


def test_circ_policy_search(app, circulation_policies):
    """Test finding a circulation policy."""
    data = [
        {
            "organisation_pid": "org1",
            "library_pid": "lib1",
            "patron_type_pid": "ptty1",
            "item_type_pid": "itty1",
            "cipo": "cipo2",
        },
        {
            "organisation_pid": "org1",
            "library_pid": "lib1",
            "patron_type_pid": "ptty2",
            "item_type_pid": "itty2",
            "cipo": "cipo3",
        },
        {
            "organisation_pid": "org1",
            "library_pid": "lib2",
            "patron_type_pid": "ptty2",
            "item_type_pid": "itty2",
            "cipo": "cipo1",
        },
        {
            "organisation_pid": "org1",
            "library_pid": "lib1",
            "patron_type_pid": "ptty3",
            "item_type_pid": "itty2",
            "cipo": "cipo1",
        },
        {
            "organisation_pid": "org1",
            "library_pid": "lib1",
            "patron_type_pid": "ptty1",
            "item_type_pid": "itty2",
            "cipo": "cipo1",
        },
        {
            "organisation_pid": "org2",
            "library_pid": "lib4",
            "patron_type_pid": "ptty3",
            "item_type_pid": "itty4",
            "cipo": "cipo4",
        },
    ]
    for row in data:
        cipo = CircPolicy.provide_circ_policy(
            row["organisation_pid"],
            row["library_pid"],
            row["patron_type_pid"],
            row["item_type_pid"],
        )
        assert cipo.pid == row["cipo"]
