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

"""Organisation Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.organisations.api import \
    organisation_id_fetcher as fetcher


def test_organisation_libararies(org_martigny, lib_martigny):
    """Test libraries retrival."""
    assert list(org_martigny.get_libraries()) == [lib_martigny]


def test_organisation_create(app, db, org_martigny_data):
    """Test organisation creation."""
    org = Organisation.create(org_martigny_data, delete_pid=True)
    assert org == org_martigny_data
    assert org.get('pid') == '1'

    assert org.get_links_to_me() == {}
    assert org.can_delete

    org = Organisation.get_record_by_pid('1')
    assert org == org_martigny_data

    fetched_pid = fetcher(org.id, org)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'org'
