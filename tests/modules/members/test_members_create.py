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
# as an Intergovernmental membanization or submit itself to any jurisdiction.

"""Minters module tests."""

from __future__ import absolute_import, print_function

from reroils_app.modules.members.api import Member


def test_members_create(db, minimal_member_record):
    """Test member creat."""
    from copy import deepcopy
    del minimal_member_record['$schema']
    memb_rec = deepcopy(minimal_member_record)
    memb = Member.create(minimal_member_record)
    assert memb_rec == memb


def test_memebers_create_pid(db, minimal_member_record):
    """Test member creat with pid."""
    from copy import deepcopy
    del minimal_member_record['$schema']
    memb_rec = deepcopy(minimal_member_record)
    memb = Member.create(minimal_member_record)
    memb_rec['pid'] = '1'
    assert memb_rec == memb
