# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.patrons_types.api import PatronType, PatronTypeSearch


def test_patron_type_search():
    """Validate index name."""
    assert 'patrons_types' == PatronTypeSearch.Meta.index


def test_can_delete():
    """Can Delete."""
    assert PatronType.can_delete


# TODO: Issue #45
# def test_exist_name_and_organisation_pid(app, db,
#                                          minimal_patron_type_record):
#     """Test for exist name and organisation pid."""
#     patron_type = PatronType.create(
#         minimal_patron_type_record,
#         dbcommit=True,
#         reindex=True
#     )
#
#    result = PatronType.exist_name_and_organisation_pid(
#        "Patron Type Name", "1"
#    )
