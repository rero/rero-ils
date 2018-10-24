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

import pytest

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.errors import PolicyNameAlreadyExists
from rero_ils.modules.organisations.api import Organisation
from rero_ils.test_utils import es_flush_and_refresh


def test_circ_policy_create(
        app, es,
        minimal_circ_policy_record,
        minimal_organisation_record
):
    """Test circulation policy create."""
    from copy import deepcopy
    org_rec = deepcopy(minimal_organisation_record)
    org = Organisation.create(
        minimal_organisation_record,
        dbcommit=True,
        reindex=True
    )
    assert org_rec == org
    assert org['pid'] == '1'

    circ_policy_rec = deepcopy(minimal_circ_policy_record)
    circ_policy = CircPolicy.create(
        minimal_circ_policy_record,
        dbcommit=True,
        reindex=True
    )
    assert circ_policy_rec == circ_policy
    assert circ_policy['pid'] == '1'

    es_flush_and_refresh()
    circ_policy_rec = deepcopy(minimal_circ_policy_record)
    with pytest.raises(PolicyNameAlreadyExists):
        circ_policy = CircPolicy.create(
            minimal_circ_policy_record,
            dbcommit=True,
            reindex=True
        )
        assert not circ_policy
