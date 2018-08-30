# -*- coding: utf-8 -*-
#
# This file is part of REROILS.
# Copyright (C) 2017 RERO.
#
# REROILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# REROILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REROILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Fetchers module tests."""

from __future__ import absolute_import, print_function

from uuid import uuid4

from reroils_app.modules.locations.fetchers import \
    location_id_fetcher as fetcher
from reroils_app.modules.locations.minters import location_id_minter as minter


def test_location_id_fetcher(db):
    """Test location_id fetcher."""
    data = {}
    rec_uuid = uuid4()
    minted_pid = minter(rec_uuid, data)
    fetched_pid = fetcher(rec_uuid, data)

    assert minted_pid.pid_value == fetched_pid.pid_value
    assert fetched_pid.pid_type == fetched_pid.provider.pid_type
    assert fetched_pid.pid_type == 'loc'
