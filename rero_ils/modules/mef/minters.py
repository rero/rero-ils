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

"""Identifier minters."""

from __future__ import absolute_import, print_function, unicode_literals

from .providers import MefPersonProvider


def mef_person_id_minter(record_uuid, data, pid_key='pid',
                         object_type='rec'):
    """RERIOLS Organisationid minter."""
    assert pid_key in data
    pid_value = data[pid_key]
    provider = MefPersonProvider.create(
        object_type=object_type,
        object_uuid=record_uuid,
        pid_value=pid_value
    )
    pid = provider.pid
    data[pid_key] = pid.pid_value
    return pid
