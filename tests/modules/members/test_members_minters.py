# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Minters module tests."""

from __future__ import absolute_import, print_function

from uuid import uuid4

from reroils_app.modules.members import minters


def test_organisation_id_minter(db):
    """Test member_id minter."""
    data = {}
    # first record
    rec_uuid = uuid4()
    pid1 = minters.member_id_minter(rec_uuid, data)
    assert pid1
    assert data['pid'] == pid1.pid_value
    assert data['pid'] == '1'
    assert pid1.object_type == 'rec'
    assert pid1.object_uuid == rec_uuid

    # second record
    data = {}
    rec_uuid = uuid4()
    pid2 = minters.member_id_minter(rec_uuid, data)
    assert data['pid'] == '2'
