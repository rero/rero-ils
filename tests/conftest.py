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
from rero_ils.modules.items_types.api import ItemType
from rero_ils.modules.libraries_locations.api import LibraryWithLocations
from rero_ils.modules.locations.api import Location

# TODO: get url dynamiclly
url_schema = 'http://ils.test.rero.ch/schema'


@pytest.fixture(scope='module')
def app_config(app_config):
    """Create temporary instance dir for each test."""
    app_config['RATELIMIT_STORAGE_URL'] = 'memory://'
    app_config['CACHE_TYPE'] = 'simple'
    app_config['SEARCH_ELASTIC_HOSTS'] = None
    app_config['JSONSCHEMAS_HOST'] = 'ils.test.rero.ch'
    app_config['JSONSCHEMAS_ENDPOINT'] = '/schema'
    return app_config


@pytest.yield_fixture()
def minimal_library_record():
    """Simple library record."""
    yield {
        '$schema': url_schema + '/libraries/library-v0.0.1.json',
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
        'item_type_pid': '1',
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
                'pickup_library_pid': '1'
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
        'item_type_pid': '1',
        '_circulation': {
            'holdings': [{
                'patron_barcode': '654321',
                'start_date': '2018-10-10',
                'end_date': '2018-11-10',
                'pickup_library_pid': '1'
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
        'item_type_pid': '1',
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
        'item_type_pid': '1',
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
        'item_type_pid': '1',
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
        'library_pid': '1',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type_pid': '1'
    }


@pytest.yield_fixture()
def minimal_patron_type_record():
    """Patron Type minimal record."""
    yield {
        '$schema': url_schema + '/patrons_types/patron_type-v0.0.1.json',
        'pid': '1',
        'name': 'Patron Type Name',
        'description': 'Patron Type Description',
        'organisation_pid': '1'
    }


@pytest.yield_fixture()
def minimal_item_type_record():
    """Item Type minimal record."""
    yield {
        '$schema': url_schema + '/items_types/item_type-v0.0.1.json',
        'pid': '1',
        'name': 'Item Type Name',
        'description': 'Item Type Description',
        'organisation_pid': '1'
    }


@pytest.yield_fixture()
def create_minimal_resources(db, es, minimal_library_record,
                             minimal_location_record,
                             minimal_item_record,
                             minimal_document_record,
                             minimal_item_type_record):
    """Minimal resources."""
    ItemType.create(minimal_item_type_record,
                    dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(minimal_library_record,
                                          dbcommit=True, reindex=True)
    location = Location.create(minimal_location_record,
                               dbcommit=True, reindex=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record,
                                    dbcommit=True, reindex=True)
    item = Item.create(minimal_item_record,
                       dbcommit=True, reindex=True)
    doc.add_item(item,
                 dbcommit=True, reindex=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf(db, minimal_library_record,
                                      minimal_location_record,
                                      item_record_on_shelf,
                                      minimal_document_record,
                                      minimal_item_type_record):
    """Minimal resources on_shelf."""
    ItemType.create(minimal_item_type_record,
                    dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True
    )
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf_req(db, minimal_library_record,
                                          minimal_location_record,
                                          item_record_on_shelf_requested,
                                          minimal_document_record,
                                          minimal_item_type_record):
    """Minimal resources on_shelf req."""
    ItemType.create(minimal_item_type_record,
                    dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True
    )
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf_requested, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_in_transit(db, minimal_library_record,
                                        minimal_location_record,
                                        item_record_in_transit,
                                        minimal_document_record,
                                        minimal_item_type_record):
    """Minimal resources in_transit."""
    ItemType.create(minimal_item_type_record,
                    dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True
    )
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_in_transit, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_on_loan(db, minimal_library_record,
                                     minimal_location_record,
                                     item_record_on_loan,
                                     minimal_document_record,
                                     minimal_item_type_record):
    """Minimal resources on_loan."""
    ItemType.create(minimal_item_type_record,
                    dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True
    )
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_loan, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location
