# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
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

"""Utils tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.items.cli import get_one_patron, get_one_staff_user


def test_items_cli_one_patron(app, all_resources_limited, es_clear):
    """Item cli utils."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    patron = get_one_patron(exclude_this_barcode=simonetta.barcode)
    assert patron.barcode == philippe.barcode
    patron = get_one_patron(exclude_this_barcode=philippe.barcode)
    assert patron.barcode == simonetta.barcode


def test_items_cli_one_staff_user(app, all_resources_limited, es_clear):
    """Item cli utils."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    patron = get_one_staff_user()
    assert (
        patron.barcode == philippe.barcode or
        patron.barcode == simonetta.barcode
    )
