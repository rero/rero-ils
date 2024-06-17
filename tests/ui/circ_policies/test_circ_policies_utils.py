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

"""Circulation policies tests."""

from __future__ import absolute_import, print_function

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
