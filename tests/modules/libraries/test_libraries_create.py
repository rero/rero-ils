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

from rero_ils.modules.libraries.api import Library


def test_libraries_create(db, minimal_library_record):
    """Test library creat."""
    from copy import deepcopy

    del minimal_library_record['$schema']
    lib_rec = deepcopy(minimal_library_record)
    lib = Library.create(minimal_library_record)
    assert lib_rec == lib


def test_libraries_create_pid(db, minimal_library_record):
    """Test library creat with pid."""
    from copy import deepcopy

    del minimal_library_record['$schema']
    lib_rec = deepcopy(minimal_library_record)
    lib = Library.create(minimal_library_record)
    lib_rec['pid'] = '1'
    assert lib_rec == lib
