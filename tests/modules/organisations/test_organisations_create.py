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

from reroils_app.modules.organisations.api import Organisation


def test_organisation_create(db, minimal_organisation_record):
    """Test organisation creat."""
    from copy import deepcopy
    org_rec = deepcopy(minimal_organisation_record)
    org = Organisation.create(minimal_organisation_record)
    assert org_rec == org


def test_organisation_create_pid(db, minimal_organisation_record):
    """Test organisation creat with pid."""
    org = Organisation.create(minimal_organisation_record)
    assert org['pid'] == '1'
