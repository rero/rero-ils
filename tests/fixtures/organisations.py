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

"""Common pytest fixtures and plugins."""

from copy import deepcopy

import pytest
from utils import flush_index

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy
from rero_ils.modules.item_types.api import ItemType, ItemTypesSearch
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.organisations.api import Organisation, OrganisationSearch
from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch


@pytest.fixture(scope="module")
def org_martigny_data(data):
    """Martigny organisation data."""
    return (data.get('org1'))


@pytest.fixture(scope="module")
def org_martigny(app, org_martigny_data):
    """Create Martigny organisation."""
    org = Organisation.create(
        data=org_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(OrganisationSearch.Meta.index)
    return org


@pytest.fixture(scope="function")
def organisation_temp(app, org_martigny):
    """Scope function organisation data."""
    org = Organisation.create(
        data=org_martigny,
        dbcommit=True,
        delete_pid=True,
        reindex=True)
    flush_index(OrganisationSearch.Meta.index)
    return org


@pytest.fixture(scope="module")
def org_sion_data(data):
    """Sion organisation data.."""
    return (data.get('org2'))


@pytest.fixture(scope="module")
def org_sion(app, org_sion_data):
    """Create Sion organisation."""
    org = Organisation.create(
        data=org_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(OrganisationSearch.Meta.index)
    return org


@pytest.fixture(scope="module")
def lib_martigny_data(data):
    """Martigny-ville library data."""
    return deepcopy(data.get('lib1'))


@pytest.fixture(scope="module")
def lib_martigny(app, org_martigny, lib_martigny_data):
    """Martigny-ville library."""
    lib = Library.create(
        data=lib_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LibrariesSearch.Meta.index)
    return lib


@pytest.fixture(scope="module")
def lib_saxon_data(data):
    """Saxon library data."""
    return deepcopy(data.get('lib2'))


@pytest.fixture(scope="module")
def lib_saxon(app, org_martigny, lib_saxon_data):
    """Saxon library."""
    lib = Library.create(
        data=lib_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LibrariesSearch.Meta.index)
    return lib


@pytest.fixture(scope="module")
def lib_fully_data(data):
    """Fully library data."""
    return deepcopy(data.get('lib3'))


@pytest.fixture(scope="module")
def lib_fully(app, org_martigny, lib_fully_data):
    """Fully library."""
    lib = Library.create(
        data=lib_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LibrariesSearch.Meta.index)
    return lib


@pytest.fixture(scope="module")
def lib_sion_data(data):
    """Sion library data."""
    return deepcopy(data.get('lib4'))


@pytest.fixture(scope="module")
def lib_sion(app, org_sion, lib_sion_data):
    """Sion library."""
    lib = Library.create(
        data=lib_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LibrariesSearch.Meta.index)
    return lib


@pytest.fixture(scope="module")
def lib_aproz_data(data):
    """Aproz library data."""
    return deepcopy(data.get('lib5'))


@pytest.fixture(scope="module")
def lib_aproz(app, org_sion, lib_aproz_data):
    """Aproz library."""
    lib = Library.create(
        data=lib_aproz_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LibrariesSearch.Meta.index)
    return lib


@pytest.fixture(scope="module")
def loc_public_martigny_data(data):
    """Load public space location for Martigny ville."""
    return deepcopy(data.get('loc1'))


@pytest.fixture(scope="module")
def loc_restricted_martigny_data(data):
    """Load restricted space location for Martigny ville."""
    return deepcopy(data.get('loc2'))


@pytest.fixture(scope="module")
def loc_public_saxon_data(data):
    """Load public space location for Saxon."""
    return deepcopy(data.get('loc3'))


@pytest.fixture(scope="module")
def loc_restricted_saxon_data(data):
    """Load restricted space location for saxon."""
    return deepcopy(data.get('loc4'))


@pytest.fixture(scope="module")
def loc_public_fully_data(data):
    """Load public space location for Fully."""
    return deepcopy(data.get('loc5'))


@pytest.fixture(scope="module")
def loc_restricted_fully_data(data):
    """Load restricted space location for Fully."""
    return deepcopy(data.get('loc6'))


@pytest.fixture(scope="module")
def loc_public_sion_data(data):
    """Load public space location for Sion."""
    return deepcopy(data.get('loc7'))


@pytest.fixture(scope="module")
def loc_restricted_sion_data(data):
    """Load restricted space location for Sion."""
    return deepcopy(data.get('loc8'))


@pytest.fixture(scope="module")
def loc_public_martigny(app, lib_martigny, loc_public_martigny_data):
    """Create public space location for Martigny ville."""
    loc = Location.create(
        data=loc_public_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_restricted_martigny(app, lib_martigny, loc_restricted_martigny_data):
    """Create restricted space location for Martigny ville."""
    loc = Location.create(
        data=loc_restricted_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_public_saxon(app, lib_saxon, loc_public_saxon_data):
    """Create public space location for saxon."""
    loc = Location.create(
        data=loc_public_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_restricted_saxon(app, lib_saxon, loc_restricted_saxon_data):
    """Create restricted space location for saxon."""
    loc = Location.create(
        data=loc_restricted_saxon_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_public_fully(app, lib_fully, loc_public_fully_data):
    """Create public space location for fully."""
    loc = Location.create(
        data=loc_public_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_restricted_fully(app, lib_fully, loc_restricted_fully_data):
    """Create restricted space location for fully."""
    loc = Location.create(
        data=loc_restricted_fully_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_public_sion(app, lib_sion, loc_public_sion_data):
    """Create public space location for sion."""
    loc = Location.create(
        data=loc_public_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="module")
def loc_restricted_sion(app, lib_sion, loc_restricted_sion_data):
    """Create restricted space location for sion."""
    loc = Location.create(
        data=loc_restricted_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(LocationsSearch.Meta.index)
    return loc


@pytest.fixture(scope="function")
def item_type_data_tmp(data):
    """Load standard item type of martigny."""
    return deepcopy(data.get('itty1'))


@pytest.fixture(scope="module")
def item_type_standard_martigny_data(data):
    """Load standard item type of martigny."""
    return deepcopy(data.get('itty1'))


@pytest.fixture(scope="module")
def item_type_standard_martigny(
        app, org_martigny, item_type_standard_martigny_data):
    """Create standard item type of martigny."""
    itty = ItemType.create(
        data=item_type_standard_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def item_type_on_site_martigny_data(data):
    """Load on-site item type of martigny."""
    return deepcopy(data.get('itty2'))


@pytest.fixture(scope="module")
def item_type_on_site_martigny(
        app, org_martigny, item_type_on_site_martigny_data):
    """Create on_site item type of martigny."""
    itty = ItemType.create(
        data=item_type_on_site_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def item_type_specific_martigny_data(data):
    """Load specific item type of martigny."""
    return deepcopy(data.get('itty3'))


@pytest.fixture(scope="module")
def item_type_specific_martigny(
        app, org_martigny, item_type_specific_martigny_data):
    """Create specific item type of martigny."""
    itty = ItemType.create(
        data=item_type_specific_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def item_type_regular_sion_data(data):
    """Load regular item type of sion."""
    return deepcopy(data.get('itty4'))


@pytest.fixture(scope="module")
def item_type_regular_sion(
        app, org_sion, item_type_regular_sion_data):
    """Create regular item type of sion."""
    itty = ItemType.create(
        data=item_type_regular_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def item_type_internal_sion_data(data):
    """Load internal item type of sion."""
    return deepcopy(data.get('itty5'))


@pytest.fixture(scope="module")
def item_type_internal_sion(
        app, org_sion, item_type_internal_sion_data):
    """Create internal item type of sion."""
    itty = ItemType.create(
        data=item_type_internal_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def item_type_particular_sion_data(data):
    """Load particular item type of sion."""
    return deepcopy(data.get('itty6'))


@pytest.fixture(scope="module")
def item_type_particular_sion(
        app, org_sion, item_type_particular_sion_data):
    """Create particular item type of sion."""
    itty = ItemType.create(
        data=item_type_particular_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(ItemTypesSearch.Meta.index)
    return itty


@pytest.fixture(scope="module")
def patron_type_children_martigny_data(data):
    """Load children patron type of martigny."""
    return deepcopy(data.get('ptty1'))


@pytest.fixture(scope="function")
def patron_type_data_tmp(data):
    """Load children patron type of martigny scope function."""
    return deepcopy(data.get('ptty1'))


@pytest.fixture(scope="function")
def patron_type_tmp(db, patron_type_children_martigny_data):
    """Create scope function children patron type of martigny."""
    ptty = PatronType.create(
        data=patron_type_children_martigny_data,
        dbcommit=True,
        delete_pid=True)
    return ptty


@pytest.fixture(scope="module")
def patron_type_children_martigny(
        app, org_martigny, patron_type_children_martigny_data):
    """Create children patron type of martigny."""
    ptty = PatronType.create(
        data=patron_type_children_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronTypesSearch.Meta.index)
    return ptty


@pytest.fixture(scope="module")
def patron_type_adults_martigny_data(data):
    """Load adults patron type of martigny."""
    return deepcopy(data.get('ptty2'))


@pytest.fixture(scope="module")
def patron_type_adults_martigny(
        app, org_martigny, patron_type_adults_martigny_data):
    """Create adults patron type of martigny."""
    ptty = PatronType.create(
        data=patron_type_adults_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronTypesSearch.Meta.index)
    return ptty


@pytest.fixture(scope="module")
def patron_type_youngsters_sion_data(data):
    """Load youngsters patron type of sion."""
    return deepcopy(data.get('ptty3'))


@pytest.fixture(scope="module")
def patron_type_youngsters_sion(
        app, org_sion, patron_type_youngsters_sion_data):
    """Crate youngsters patron type of sion."""
    ptty = PatronType.create(
        data=patron_type_youngsters_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronTypesSearch.Meta.index)
    return ptty


@pytest.fixture(scope="module")
def patron_type_grown_sion_data(data):
    """Load grown patron type of sion."""
    return deepcopy(data.get('ptty4'))


@pytest.fixture(scope="module")
def patron_type_grown_sion(
        app, org_sion, patron_type_grown_sion_data):
    """Crate grown patron type of sion."""
    ptty = PatronType.create(
        data=patron_type_grown_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(PatronTypesSearch.Meta.index)
    return ptty


@pytest.fixture(scope="function")
def circ_policy_martigny_data_tmp(data):
    """Load default circ policy for organisation martigny scope function."""
    return deepcopy(data.get('cipo1'))


@pytest.fixture(scope="module")
def circ_policy_default_martigny_data(data):
    """Load default circ policy for organisation martigny."""
    return deepcopy(data.get('cipo1'))


@pytest.fixture(scope="module")
def circ_policy_default_martigny(
        app, org_martigny, circ_policy_default_martigny_data):
    """Create default circ policy for organisation martigny."""
    cipo = CircPolicy.create(
        data=circ_policy_default_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    return cipo


@pytest.fixture(scope="module")
def circ_policy_default_sion_data(data):
    """Load default circ policy for organisation sion."""
    return deepcopy(data.get('cipo4'))


@pytest.fixture(scope="module")
def circ_policy_default_sion(
        app, org_sion, circ_policy_default_sion_data):
    """Create default circ policy for organisation sion."""
    cipo = CircPolicy.create(
        data=circ_policy_default_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    return cipo


@pytest.fixture(scope="module")
def circ_policy_short_martigny_data(data):
    """Load short circ policy for organisation martigny."""
    return deepcopy(data.get('cipo2'))


@pytest.fixture(scope="module")
def circ_policy_short_martigny(
        app,
        patron_type_children_martigny,
        patron_type_adults_martigny,
        item_type_standard_martigny,
        item_type_specific_martigny,
        circ_policy_short_martigny_data):
    """Create short circ policy for organisation martigny."""
    cipo = CircPolicy.create(
        data=circ_policy_short_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    return cipo


@pytest.fixture(scope="module")
def circ_policy_temp_martigny_data(data):
    """Load temporary circ policy for organisation martigny.

    library martigny-ville.
    """
    return deepcopy(data.get('cipo3'))


@pytest.fixture(scope="module")
def circ_policy_temp_martigny(
        app,
        lib_martigny,
        patron_type_adults_martigny,
        item_type_on_site_martigny,
        circ_policy_temp_martigny_data):
    """Create temporary circ policy for organisation martigny.

    library martigny.
    """
    cipo = CircPolicy.create(
        data=circ_policy_temp_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    return cipo


@pytest.fixture(scope="module")
def circulation_policies(
        circ_policy_default_martigny,
        circ_policy_default_sion,
        circ_policy_short_martigny,
        circ_policy_temp_martigny):
    """Load all circulation policies."""
    return [
        circ_policy_default_martigny,
        circ_policy_default_sion,
        circ_policy_short_martigny,
        circ_policy_temp_martigny
    ]
