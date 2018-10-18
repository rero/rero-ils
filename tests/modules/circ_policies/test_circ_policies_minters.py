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

"""Minters module tests."""

from __future__ import absolute_import, print_function

from uuid import uuid4

from rero_ils.modules.circ_policies import minters


def test_circ_policy_id_minter(db):
    """Test circ_policy_id minter."""
    data = {}
    # first record
    rec_uuid = uuid4()
    pid1 = minters.circ_policy_id_minter(rec_uuid, data)
    assert pid1
    assert data['pid'] == pid1.pid_value
    assert data['pid'] == '1'
    assert pid1.object_type == 'rec'
    assert pid1.object_uuid == rec_uuid

    # second record
    data = {}
    rec_uuid = uuid4()
    pid2 = minters.circ_policy_id_minter(rec_uuid, data)
    assert pid2
    assert data['pid'] == '2'
