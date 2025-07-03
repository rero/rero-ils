# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Common pytest fixtures and plugins."""

from copy import deepcopy

import pytest

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy
from rero_ils.modules.collections.api import Collection, CollectionsSearch
from rero_ils.modules.item_types.api import ItemType, ItemTypesSearch
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.organisations.api import Organisation, OrganisationsSearch
from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch


@pytest.fixture(scope="module")
def org_martigny_data(data):
    """Martigny organisation data."""
    return data.get("org1")


@pytest.fixture(scope="module")
def org_martigny(app, org_martigny_data):
    """Create Martigny organisation."""
    org = Organisation.create(
        data=org_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    OrganisationsSearch.flush_and_refresh()
    return org


@pytest.fixture(scope="function")
def organisation_temp(app, org_martigny):
    """Scope function organisation data."""
    org = Organisation.create(
        data=org_martigny, dbcommit=True, delete_pid=True, reindex=True
    )
    OrganisationsSearch.flush_and_refresh()
    return org


@pytest.fixture(scope="module")
def org_sion_data(data):
    """Sion organisation data.."""
    return data.get("org2")


@pytest.fixture(scope="module")
def org_sion(app, org_sion_data):
    """Create Sion organisation."""
    org = Organisation.create(
        data=org_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    OrganisationsSearch.flush_and_refresh()
    return org


@pytest.fixture(scope="module")
def lib_martigny_data(data):
    """Martigny-ville library data."""
    return deepcopy(data.get("lib1"))


@pytest.fixture(scope="module")
def lib_martigny_bourg_data(data):
    """Martigny-bourg library data."""
    return deepcopy(data.get("lib7"))


@pytest.fixture(scope="module")
def lib_martigny(app, org_martigny, lib_martigny_data):
    """Martigny-ville library."""
    lib = Library.create(
        data=lib_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def lib_martigny_bourg(app, org_martigny, lib_martigny_bourg_data):
    """Martigny-bourg library."""
    lib = Library.create(
        data=lib_martigny_bourg_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def lib_saillon_data(data):
    """Saillon library data."""
    return deepcopy(data.get("lib6"))


@pytest.fixture(scope="module")
def lib_saillon(app, org_martigny, lib_saillon_data):
    """Saillon library."""
    lib = Library.create(
        data=lib_saillon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def lib_saxon_data(data):
    """Saxon library data."""
    return deepcopy(data.get("lib2"))


@pytest.fixture(scope="module")
def lib_saxon(app, org_martigny, lib_saxon_data):
    """Saxon library."""
    lib = Library.create(
        data=lib_saxon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def lib_fully_data(data):
    """Fully library data."""
    return deepcopy(data.get("lib3"))


@pytest.fixture(scope="module")
def lib_fully(app, org_martigny, lib_fully_data):
    """Fully library."""
    lib = Library.create(
        data=lib_fully_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def lib_sion_data(data):
    """Sion library data."""
    return deepcopy(data.get("lib4"))


@pytest.fixture(scope="module")
def lib_sion(app, org_sion, lib_sion_data):
    """Sion library."""
    lib = Library.create(
        data=lib_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def lib_aproz_data(data):
    """Aproz library data."""
    return deepcopy(data.get("lib5"))


@pytest.fixture(scope="module")
def lib_aproz(app, org_sion, lib_aproz_data):
    """Aproz library."""
    lib = Library.create(
        data=lib_aproz_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LibrariesSearch.flush_and_refresh()
    return lib


@pytest.fixture(scope="module")
def loc_public_martigny_data(data):
    """Load public space location for Martigny ville."""
    return deepcopy(data.get("loc1"))


@pytest.fixture(scope="module")
def loc_public_martigny_bourg_data(data):
    """Load public space location for Martigny bourg."""
    return deepcopy(data.get("loc15"))


@pytest.fixture(scope="module")
def loc_restricted_martigny_bourg_data(data):
    """Load restricted space location for Martigny bourg."""
    return deepcopy(data.get("loc16"))


@pytest.fixture(scope="module")
def loc_public_saillon_data(data):
    """Load public space location for Saillon."""
    return deepcopy(data.get("loc14"))


@pytest.fixture(scope="module")
def loc_restricted_martigny_data(data):
    """Load restricted space location for Martigny ville."""
    return deepcopy(data.get("loc2"))


@pytest.fixture(scope="module")
def loc_public_saxon_data(data):
    """Load public space location for Saxon."""
    return deepcopy(data.get("loc3"))


@pytest.fixture(scope="module")
def loc_restricted_saxon_data(data):
    """Load restricted space location for saxon."""
    return deepcopy(data.get("loc4"))


@pytest.fixture(scope="module")
def loc_public_fully_data(data):
    """Load public space location for Fully."""
    return deepcopy(data.get("loc5"))


@pytest.fixture(scope="module")
def loc_restricted_fully_data(data):
    """Load restricted space location for Fully."""
    return deepcopy(data.get("loc6"))


@pytest.fixture(scope="module")
def loc_public_sion_data(data):
    """Load public space location for Sion."""
    return deepcopy(data.get("loc7"))


@pytest.fixture(scope="module")
def loc_restricted_sion_data(data):
    """Load restricted space location for Sion."""
    return deepcopy(data.get("loc8"))


@pytest.fixture(scope="module")
def loc_online_martigny_data(data):
    """Load online space location for Martigny."""
    return deepcopy(data.get("loc9"))


@pytest.fixture(scope="module")
def loc_online_saxon_data(data):
    """Load online space location for Saxon."""
    return deepcopy(data.get("loc10"))


@pytest.fixture(scope="module")
def loc_online_fully_data(data):
    """Load online space location for Fully."""
    return deepcopy(data.get("loc11"))


@pytest.fixture(scope="module")
def loc_online_sion_data(data):
    """Load online space location for Sion."""
    return deepcopy(data.get("loc12"))


@pytest.fixture(scope="module")
def loc_online_aproz_data(data):
    """Load online space location for Aproz."""
    return deepcopy(data.get("loc13"))


@pytest.fixture(scope="module")
def locations(
    loc_public_martigny,
    loc_restricted_martigny,
    loc_public_saxon,
    loc_restricted_saxon,
    loc_public_fully,
    loc_restricted_fully,
    loc_public_sion,
    loc_restricted_sion,
    loc_online_martigny,
    loc_online_saxon,
    loc_online_fully,
    loc_online_sion,
    loc_online_aproz,
):
    """Create all locations."""
    return [
        loc_public_martigny,
        loc_restricted_martigny,
        loc_public_saxon,
        loc_restricted_saxon,
        loc_public_fully,
        loc_restricted_fully,
        loc_public_sion,
        loc_restricted_sion,
        loc_online_martigny,
        loc_online_saxon,
        loc_online_fully,
        loc_online_sion,
        loc_online_aproz,
    ]


@pytest.fixture(scope="module")
def loc_public_martigny(app, lib_martigny, loc_public_martigny_data):
    """Create public space location for Martigny ville."""
    loc = Location.create(
        data=loc_public_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_public_martigny_bourg(app, lib_martigny_bourg, loc_public_martigny_bourg_data):
    """Create public space location for Martigny bourg."""
    loc = Location.create(
        data=loc_public_martigny_bourg_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_restricted_martigny_bourg(
    app, lib_martigny_bourg, loc_restricted_martigny_bourg_data
):
    """Create restricted space location for Martigny bourg."""
    loc = Location.create(
        data=loc_restricted_martigny_bourg_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_public_saillon(app, lib_saillon, loc_public_saillon_data):
    """Create public space location for saillon."""
    loc = Location.create(
        data=loc_public_saillon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_restricted_martigny(app, lib_martigny, loc_restricted_martigny_data):
    """Create restricted space location for Martigny ville."""
    loc = Location.create(
        data=loc_restricted_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_public_saxon(app, lib_saxon, loc_public_saxon_data):
    """Create public space location for saxon."""
    loc = Location.create(
        data=loc_public_saxon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_restricted_saxon(app, lib_saxon, loc_restricted_saxon_data):
    """Create restricted space location for saxon."""
    loc = Location.create(
        data=loc_restricted_saxon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_public_fully(app, lib_fully, loc_public_fully_data):
    """Create public space location for fully."""
    loc = Location.create(
        data=loc_public_fully_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_restricted_fully(app, lib_fully, loc_restricted_fully_data):
    """Create restricted space location for fully."""
    loc = Location.create(
        data=loc_restricted_fully_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_public_sion(app, lib_sion, loc_public_sion_data):
    """Create public space location for sion."""
    loc = Location.create(
        data=loc_public_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_restricted_sion(app, lib_sion, loc_restricted_sion_data):
    """Create restricted space location for sion."""
    loc = Location.create(
        data=loc_restricted_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_online_martigny(app, lib_martigny, loc_online_martigny_data):
    """Create online space location for Martigny."""
    loc = Location.create(
        data=loc_online_martigny_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_online_saxon(app, lib_saxon, loc_online_saxon_data):
    """Create online space location for Saxon."""
    loc = Location.create(
        data=loc_online_saxon_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_online_fully(app, lib_fully, loc_online_fully_data):
    """Create online space location for Fully."""
    loc = Location.create(
        data=loc_online_fully_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_online_sion(app, lib_sion, loc_online_sion_data):
    """Create online space location for Sion."""
    loc = Location.create(
        data=loc_online_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="module")
def loc_online_aproz(app, lib_aproz, loc_online_aproz_data):
    """Create online space location for aproz."""
    loc = Location.create(
        data=loc_online_aproz_data, delete_pid=False, dbcommit=True, reindex=True
    )
    LocationsSearch.flush_and_refresh()
    return loc


@pytest.fixture(scope="function")
def item_type_data_tmp(data):
    """Load standard item type of martigny."""
    return deepcopy(data.get("itty1"))


@pytest.fixture(scope="module")
def item_type_standard_martigny_data(data):
    """Load standard item type of martigny."""
    return deepcopy(data.get("itty1"))


@pytest.fixture(scope="module")
def item_type_standard_martigny(app, org_martigny, item_type_standard_martigny_data):
    """Create standard item type of martigny."""
    itty = ItemType.create(
        data=item_type_standard_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_on_site_martigny_data(data):
    """Load on-site item type of martigny."""
    return deepcopy(data.get("itty2"))


@pytest.fixture(scope="module")
def item_type_on_site_martigny(app, org_martigny, item_type_on_site_martigny_data):
    """Create on_site item type of martigny."""
    itty = ItemType.create(
        data=item_type_on_site_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_specific_martigny_data(data):
    """Load specific item type of martigny."""
    return deepcopy(data.get("itty3"))


@pytest.fixture(scope="module")
def item_type_specific_martigny(app, org_martigny, item_type_specific_martigny_data):
    """Create specific item type of martigny."""
    itty = ItemType.create(
        data=item_type_specific_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_regular_sion_data(data):
    """Load regular item type of sion."""
    return deepcopy(data.get("itty4"))


@pytest.fixture(scope="module")
def item_type_regular_sion(app, org_sion, item_type_regular_sion_data):
    """Create regular item type of sion."""
    itty = ItemType.create(
        data=item_type_regular_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_internal_sion_data(data):
    """Load internal item type of sion."""
    return deepcopy(data.get("itty5"))


@pytest.fixture(scope="module")
def item_type_internal_sion(app, org_sion, item_type_internal_sion_data):
    """Create internal item type of sion."""
    itty = ItemType.create(
        data=item_type_internal_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_particular_sion_data(data):
    """Load particular item type of sion."""
    return deepcopy(data.get("itty6"))


@pytest.fixture(scope="module")
def item_type_particular_sion(app, org_sion, item_type_particular_sion_data):
    """Create particular item type of sion."""
    itty = ItemType.create(
        data=item_type_particular_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_online_martigny_data(data):
    """Load onine item type of martigny."""
    return deepcopy(data.get("itty7"))


@pytest.fixture(scope="module")
def item_type_online_martigny(app, org_martigny, item_type_online_martigny_data):
    """Create particular item type of martigny."""
    itty = ItemType.create(
        data=item_type_online_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_online_sion_data(data):
    """Load particular item type of sion."""
    return deepcopy(data.get("itty8"))


@pytest.fixture(scope="module")
def item_type_online_sion(app, org_sion, item_type_online_sion_data):
    """Create particular item type of sion."""
    itty = ItemType.create(
        data=item_type_online_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def item_type_missing_martigny_data(data):
    """Load missing item type of martigny."""
    return deepcopy(data.get("itty9"))


@pytest.fixture(scope="module")
def item_type_missing_martigny(app, org_martigny, item_type_missing_martigny_data):
    """Create missing item type of martigny."""
    itty = ItemType.create(
        data=item_type_missing_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    ItemTypesSearch.flush_and_refresh()
    return itty


@pytest.fixture(scope="module")
def patron_type_children_martigny_data(data):
    """Load children patron type of martigny."""
    return deepcopy(data.get("ptty1"))


@pytest.fixture(scope="function")
def patron_type_data_tmp(data):
    """Load children patron type of martigny scope function."""
    return deepcopy(data.get("ptty1"))


@pytest.fixture(scope="function")
def patron_type_tmp(db, org_martigny, patron_type_children_martigny_data):
    """Create scope function children patron type of martigny."""
    return PatronType.create(
        data=patron_type_children_martigny_data, dbcommit=True, delete_pid=True
    )


@pytest.fixture(scope="module")
def patron_type_children_martigny(
    app, org_martigny, patron_type_children_martigny_data
):
    """Create children patron type of martigny."""
    ptty = PatronType.create(
        data=patron_type_children_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    PatronTypesSearch.flush_and_refresh()
    return ptty


@pytest.fixture(scope="module")
def patron_type_adults_martigny_data(data):
    """Load adults patron type of martigny."""
    return deepcopy(data.get("ptty2"))


@pytest.fixture(scope="module")
def patron_type_adults_martigny(app, org_martigny, patron_type_adults_martigny_data):
    """Create adults patron type of martigny."""
    ptty = PatronType.create(
        data=patron_type_adults_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    PatronTypesSearch.flush_and_refresh()
    return ptty


@pytest.fixture(scope="module")
def patron_type_youngsters_sion_data(data):
    """Load youngsters patron type of sion."""
    return deepcopy(data.get("ptty3"))


@pytest.fixture(scope="module")
def patron_type_youngsters_sion(app, org_sion, patron_type_youngsters_sion_data):
    """Crate youngsters patron type of sion."""
    ptty = PatronType.create(
        data=patron_type_youngsters_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    PatronTypesSearch.flush_and_refresh()
    return ptty


@pytest.fixture(scope="module")
def patron_type_grown_sion_data(data):
    """Load grown patron type of sion."""
    return deepcopy(data.get("ptty4"))


@pytest.fixture(scope="module")
def patron_type_grown_sion(app, org_sion, patron_type_grown_sion_data):
    """Crate grown patron type of sion."""
    ptty = PatronType.create(
        data=patron_type_grown_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    PatronTypesSearch.flush_and_refresh()
    return ptty


@pytest.fixture(scope="function")
def circ_policy_martigny_data_tmp(data):
    """Load default circ policy for organisation martigny scope function."""
    return deepcopy(data.get("cipo1"))


@pytest.fixture(scope="module")
def circ_policy_default_martigny_data(data):
    """Load default circ policy for organisation martigny."""
    return deepcopy(data.get("cipo1"))


@pytest.fixture(scope="module")
def circ_policy_default_martigny(
    app, org_martigny, lib_martigny, lib_saxon, circ_policy_default_martigny_data
):
    """Create default circ policy for organisation martigny."""
    cipo = CircPolicy.create(
        data=circ_policy_default_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circ_policy_default_sion_data(data):
    """Load default circ policy for organisation sion."""
    return deepcopy(data.get("cipo4"))


@pytest.fixture(scope="module")
def circ_policy_default_sion(app, org_sion, lib_sion, circ_policy_default_sion_data):
    """Create default circ policy for organisation sion."""
    cipo = CircPolicy.create(
        data=circ_policy_default_sion_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circ_policy_short_martigny_data(data):
    """Load short circ policy for organisation martigny."""
    return deepcopy(data.get("cipo2"))


@pytest.fixture(scope="module")
def circ_policy_short_martigny(
    app,
    patron_type_children_martigny,
    patron_type_adults_martigny,
    item_type_standard_martigny,
    item_type_specific_martigny,
    circ_policy_short_martigny_data,
):
    """Create short circ policy for organisation martigny."""
    cipo = CircPolicy.create(
        data=circ_policy_short_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circ_policy_temp_martigny_data(data):
    """Load temporary circ policy for organisation martigny.

    library martigny-ville.
    """
    return deepcopy(data.get("cipo3"))


@pytest.fixture(scope="module")
def circ_policy_temp_martigny(
    app,
    lib_martigny,
    patron_type_adults_martigny,
    item_type_on_site_martigny,
    circ_policy_temp_martigny_data,
):
    """Create temporary circ policy for organisation martigny.

    library martigny.
    """
    cipo = CircPolicy.create(
        data=circ_policy_temp_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circ_policy_ebooks_martigny_data(data):
    """Load ebooks circ policy for organisation martigny."""
    return deepcopy(data.get("cipo5"))


@pytest.fixture(scope="module")
def circ_policy_ebooks_martigny(
    app,
    patron_type_adults_martigny,
    patron_type_children_martigny,
    item_type_online_martigny,
    circ_policy_ebooks_martigny_data,
):
    """Create ebooks circ policy for organisation martigny."""
    cipo = CircPolicy.create(
        data=circ_policy_ebooks_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circ_policy_ebooks_sion_data(data):
    """Load ebooks circ policy for organisation sion."""
    return deepcopy(data.get("cipo6"))


@pytest.fixture(scope="module")
def circ_policy_ebooks_sion(
    app,
    patron_type_youngsters_sion,
    patron_type_grown_sion,
    item_type_online_sion,
    circ_policy_ebooks_sion_data,
):
    """Create ebooks circ policy for organisation sion."""
    cipo = CircPolicy.create(
        data=circ_policy_ebooks_sion_data, delete_pid=False, dbcommit=True, reindex=True
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circ_policy_less_than_one_day_martigny_data(data):
    """Load short circ policy for organisation martigny."""
    return deepcopy(data.get("cipo7"))


@pytest.fixture(scope="module")
def circ_policy_less_than_one_day_martigny(
    app,
    patron_type_adults_martigny,
    item_type_standard_martigny,
    circ_policy_less_than_one_day_martigny_data,
):
    """Create short circ policy for organisation martigny."""
    cipo = CircPolicy.create(
        data=circ_policy_less_than_one_day_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True,
    )
    CircPoliciesSearch.flush_and_refresh()
    return cipo


@pytest.fixture(scope="module")
def circulation_policies(
    circ_policy_default_martigny,
    circ_policy_default_sion,
    circ_policy_short_martigny,
    circ_policy_temp_martigny,
    circ_policy_ebooks_martigny,
    circ_policy_ebooks_sion,
):
    """Load all circulation policies."""
    return [
        circ_policy_default_martigny,
        circ_policy_default_sion,
        circ_policy_short_martigny,
        circ_policy_temp_martigny,
        circ_policy_ebooks_martigny,
        circ_policy_ebooks_sion,
        circ_policy_less_than_one_day_martigny,
    ]


@pytest.fixture(scope="module")
def coll_martigny_1_data(data):
    """Load collection Martigny 1."""
    return deepcopy(data.get("coll_martigny_1"))


@pytest.fixture(scope="module")
def coll_martigny_1(
    app, org_martigny, coll_martigny_1_data, item_lib_martigny, item2_lib_martigny
):
    """Create collection Martigny 1."""
    coll = Collection.create(
        data=coll_martigny_1_data, delete_pid=False, dbcommit=True, reindex=True
    )
    CollectionsSearch.flush_and_refresh()
    return coll


@pytest.fixture(scope="module")
def coll_sion_1_data(data):
    """Load collection Sion 1."""
    return deepcopy(data.get("coll_sion_1"))


@pytest.fixture(scope="module")
def coll_sion_1(
    app, org_sion, lib_sion, coll_sion_1_data, item_lib_sion, item2_lib_sion
):
    """Create collection Sion 1."""
    coll = Collection.create(
        data=coll_sion_1_data, delete_pid=False, dbcommit=True, reindex=True
    )
    CollectionsSearch.flush_and_refresh()
    return coll


@pytest.fixture(scope="module")
def coll_saxon_1_data(data):
    """Load collection Saxon 1."""
    return deepcopy(data.get("coll_saxon_1"))


@pytest.fixture(scope="module")
def coll_saxon_1(
    app,
    org_martigny,
    lib_saxon,
    coll_saxon_1_data,
    item2_lib_martigny,
    item_lib_martigny,
):
    """Create collection Saxon 1."""
    coll = Collection.create(
        data=coll_saxon_1_data, delete_pid=False, dbcommit=True, reindex=True
    )
    CollectionsSearch.flush_and_refresh()
    return coll
