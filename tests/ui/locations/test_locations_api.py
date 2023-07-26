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

"""Location Record tests."""

from __future__ import absolute_import, print_function

from utils import flush_index

from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.utils import get_ref_for_pid


def test_location_cannot_delete(item_lib_martigny):
    """Test cannot delete."""
    location_pid = item_lib_martigny.location_pid
    location = Location.get_record_by_pid(location_pid)
    can, reasons = location.can_delete
    assert not can
    assert reasons['links']['holdings'] == 1
    assert reasons['links']['items'] == 1


def test_location_organisation_pid(org_martigny, loc_public_martigny):
    """Test organisation pid has been added during the indexing."""
    location = LocationsSearch().get_record_by_pid(loc_public_martigny.pid)
    assert location.organisation.pid == org_martigny.pid


def test_location_restrict_pickup(
    loc_public_martigny, loc_restricted_martigny, loc_public_saxon,
    loc_public_martigny_data, loc_restricted_martigny_data,
    loc_public_saxon_data
):
    """Test automatic modification of restrict_pickup_to field."""
    loc_m1 = loc_public_martigny
    loc_m2 = loc_restricted_martigny
    loc_sax = loc_public_saxon

    # STEP 1 :: Init location for test
    #   * ensure `loc_m2` and `loc_sax` are pickup locations
    #   * ensure `loc_m1` defines other location as pickup restriction
    loc_m1['restrict_pickup_to'] = [
        {'$ref': get_ref_for_pid(Location, loc_m2.pid)},
        {'$ref': get_ref_for_pid(Location, loc_sax.pid)},
    ]
    loc_m1 = loc_m1.update(loc_m1, dbcommit=True, reindex=True)
    loc_m2['is_pickup'] = True
    loc_m2['pickup_name'] = 'loc_m2_pickup'
    loc_m2 = loc_m2.update(loc_m2, dbcommit=True, reindex=True)
    loc_sax['is_pickup'] = True
    loc_sax['pickup_name'] = 'loc_sax_pickup'
    loc_sax = loc_sax.update(loc_sax, dbcommit=True, reindex=True)
    flush_index(LocationsSearch.Meta.index)

    assert len(LocationsSearch()
               .get_record_by_pid(loc_m1.pid)
               .to_dict()['restrict_pickup_to']
               ) == 2

    # STEP 2 :: Define that loc_m2 isn't yet a pickup location
    #   The `loc_m1` must now only contain `loc_sax` as restriction for
    #   pickup location. ES index should also reflect this change.
    del loc_m2['is_pickup']
    loc_m2 = loc_m2.update(loc_m2, dbcommit=True, reindex=True)
    loc_m1 = Location.get_record(loc_m1.id)
    assert loc_m1.restrict_pickup_to == [loc_sax.pid]
    flush_index(LocationsSearch.Meta.index)
    es_restrictions = [
        restriction_loc.pid
        for restriction_loc in LocationsSearch()
        .get_record_by_pid(loc_m1.pid).restrict_pickup_to
    ]
    assert es_restrictions == [loc_sax.pid]

    # STEP 3 :: Define that loc_sax isn't yet a pickup location
    #   The `loc_m1` must not contain any restriction for pickup location.
    #   ES index should reflect this change`
    del loc_sax['is_pickup']
    loc_sax = loc_sax.update(loc_sax, dbcommit=True, reindex=True)
    assert 'pickup_name' not in loc_sax
    loc_m1 = Location.get_record(loc_m1.id)
    assert not loc_m1.restrict_pickup_to
    flush_index(LocationsSearch.Meta.index)
    assert 'restrict_pickup_to' not in \
           LocationsSearch().get_record_by_pid(loc_sax.pid).to_dict()

    # Reset fixtures
    loc_m1.update(loc_public_martigny_data, dbcommit=True, reindex=True)
    loc_m2.update(loc_restricted_martigny_data, dbcommit=True, reindex=True)
    loc_sax.update(loc_public_saxon_data, dbcommit=True, reindex=True)
