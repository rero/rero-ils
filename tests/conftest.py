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

import pytest

from rero_ils.modules.documents_items.api import DocumentsWithItems
from rero_ils.modules.items.api import Item
from rero_ils.modules.locations.api import Location
from rero_ils.modules.members_locations.api import MemberWithLocations

# TODO: get url dynamiclly
url_schema = 'http://ils.test.rero.ch/schema'


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Create test app."""
    from invenio_app.factory import create_app as create_ui_api

    return create_ui_api


@pytest.yield_fixture()
def minimal_member_record():
    """Simple member record."""
    yield {
        '$schema': url_schema + '/members/member-v0.0.1.json',
        'pid': '1',
        'code': 'vsmvvs',
        'name': 'MV Sion',
        'address': 'Rue Pratifori',
        'email': 'info@mv.ch'
    }


@pytest.yield_fixture()
def minimal_location_record():
    """Simple location record."""
    yield {
        '$schema': url_schema + '/locations/location-v0.0.1.json',
        'pid': '1',
        'code': 'net-store-base',
        'name': 'Store Base',
    }


@pytest.yield_fixture()
def minimal_item_record():
    """Simple item record."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '123456',
                'start_date': '2018-01-01',
                'end_date': '2018-02-01',
                'renewal_count': 0
            }, {
                'patron_barcode': '654321',
                'start_date': '2018-10-10',
                'end_date': '2018-11-10',
                'pickup_member_pid': '1'
            }],
            'status': 'on_loan'
        }
    }


@pytest.yield_fixture()
def minimal_document_record():
    """Minimal document."""
    yield {
        '$schema': url_schema + '/documents/document-v0.0.1.json',
        'pid': '2',
        'title': 'RERO21 pour les nuls : les premiers pas',
        'type': 'book',
        'languages': [{'language': 'fre'}],
    }


@pytest.yield_fixture()
def item_record_on_shelf_requested():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '654321',
                'start_date': '2018-10-10',
                'end_date': '2018-11-10',
                'pickup_member_pid': '1'
            }],
            'status': 'on_shelf'
        }
    }


@pytest.yield_fixture()
def item_record_in_transit():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [],
            'status': 'in_transit'
        }
    }


@pytest.yield_fixture()
def item_record_on_shelf():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [],
            'status': 'on_shelf'
        }
    }


@pytest.yield_fixture()
def item_record_on_loan():
    """Simple item record."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': '1',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': '1',
        'item_type': 'standard_loan',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '123456',
                'start_date': '2018-01-01',
                'end_date': '2018-02-01',
                'renewal_count': 0
            }],
            'status': 'on_loan'
        }
    }


@pytest.yield_fixture()
def minimal_patron_record():
    """Simple patron record."""
    yield {
        '$schema': url_schema + '/patrons/patron-v0.0.1.json',
        'pid': '1',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'barcode': '2050124311',
        'birth_date': '1967-06-07',
        'member_pid': '1',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type': 'standard_user'
    }


@pytest.yield_fixture()
def create_minimal_resources(db, minimal_member_record,
                             minimal_location_record, minimal_item_record,
                             minimal_document_record):
    """Minimal resources."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(minimal_item_record, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf(db, minimal_member_record,
                                      minimal_location_record,
                                      item_record_on_shelf,
                                      minimal_document_record):
    """Minimal resources on_shelf."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf_req(db, minimal_member_record,
                                          minimal_location_record,
                                          item_record_on_shelf_requested,
                                          minimal_document_record):
    """Minimal resources on_shelf req."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf_requested, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_in_transit(db, minimal_member_record,
                                        minimal_location_record,
                                        item_record_in_transit,
                                        minimal_document_record):
    """Minimal resources in_transit."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_in_transit, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location


@pytest.yield_fixture()
def create_minimal_resources_on_loan(db, minimal_member_record,
                                     minimal_location_record,
                                     item_record_on_loan,
                                     minimal_document_record):
    """Minimal resources on_loan."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    member.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_loan, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, member, location
