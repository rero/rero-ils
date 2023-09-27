# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Loans dumpers."""

from copy import deepcopy

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import PatronsSearch

from .models import LoanState


class CirculationDumper(InvenioRecordsDumper):
    """Item issue dumper for circulation actions."""

    def dump(self, record, data):
        """Dump an loan for circulation."""
        data = deepcopy(dict(record))
        # used only for pending
        data['creation_date'] = record.created

        ptrn_query = PatronsSearch()\
            .source(['patron', 'first_name', 'last_name'])\
            .filter('term', pid=record['patron_pid'])
        if ptrn_data := next(ptrn_query.scan(), None):
            data['patron'] = {}
            data['patron']['barcode'] = ptrn_data.patron.barcode.pop()
            data['patron']['name'] = ', '.join((
                ptrn_data.last_name, ptrn_data.first_name))

        if record.get('pickup_location_pid'):
            location = Location.get_record_by_pid(
                record.get('pickup_location_pid'))
            data['pickup_location'] = {
                'name': location.get('name'),
                'library_name': location.get_library().get('name'),
                'pickup_name': location.pickup_name
            }

        # Always add item destination readable information if item state is
        # 'in transit' ; much easier to know these informations for UI !
        item = record.item
        if item.status == ItemStatus.IN_TRANSIT:
            destination_loc_pid = item.location_pid
            if record.get('state') == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                destination_loc_pid = record.get('pickup_location_pid')
                # can be already computed
                if library_name := data.get(
                        'pickup_location', {}).get('library_name'):
                    data['item_destination'] = {
                        'library_name': library_name
                    }
            # do nothing is already done
            if not data.get('item_destination'):
                destination_loc = Location.get_record_by_pid(
                    destination_loc_pid)
                destination_lib = destination_loc.get_library()
                data['item_destination'] = {
                    'library_name': destination_lib.get('name')
                }
        return data
