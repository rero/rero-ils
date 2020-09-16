# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Blueprint used for loading templates."""


from rero_ils.modules.collections.api import Collection


def test_get_items(document, item_type_standard_martigny,
                   item_lib_martigny, item2_lib_martigny,
                   loc_public_martigny, coll_martigny_1):
    """Test get items."""
    result = [
        {'$schema': 'https://ils.rero.ch/schemas/items/item-v0.0.1.json',
            'barcode': '1234',
            'call_number': '00001',
            'document': {'$ref': 'https://ils.rero.ch/api/documents/doc1'},
            'holding': {'$ref': 'https://ils.rero.ch/api/holdings/1'},
            'item_type': {'$ref': 'https://ils.rero.ch/api/item_types/itty1'},
            'location': {'$ref': 'https://ils.rero.ch/api/locations/loc1'},
            'notes': [{
                'content': 'Lorem ipsum et blablabla...', 'type': 'staff_note'
            }],
            'organisation': {
                '$ref': 'https://ils.rero.ch/api/organisations/org1'
            },
            'pid': 'item1',
            'status': 'on_shelf',
            'type': 'standard'},
        {'$schema': 'https://ils.rero.ch/schemas/items/item-v0.0.1.json',
            'barcode': '8712133',
            'call_number': '001313',
            'document': {'$ref': 'https://ils.rero.ch/api/documents/doc1'},
            'holding': {'$ref': 'https://ils.rero.ch/api/holdings/1'},
            'item_type': {'$ref': 'https://ils.rero.ch/api/item_types/itty1'},
            'location': {'$ref': 'https://ils.rero.ch/api/locations/loc1'},
            'organisation': {
                '$ref': 'https://ils.rero.ch/api/organisations/org1'
            },
            'pid': 'item5',
            'status': 'on_shelf',
            'type': 'standard'
         }
    ]
    assert Collection.get_items(coll_martigny_1) == result
