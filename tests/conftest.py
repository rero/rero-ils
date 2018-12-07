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
from rero_ils.modules.organisations_libraries.api import \
    OrganisationWithLibraries
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons_types.api import PatronType

# TODO: get url dynamiclly
url_schema = 'http://ils.test.rero.ch/schema'


@pytest.yield_fixture()
def limited_organisation_record():
    """Simple organisation record."""
    yield {
        '$schema': url_schema + '/organisations/organisation-v0.0.1.json',
        'pid': 'organisation_pid_1',
        'name': 'MV Sion',
        'address': 'address',
    }


@pytest.yield_fixture()
def limited_organisation_record_2():
    """Simple organisation record."""
    yield {
        '$schema': url_schema + '/organisations/organisation-v0.0.1.json',
        'pid': 'organisation_pid_2',
        'name': 'MV Martigny',
        'address': 'address',
    }


@pytest.yield_fixture()
def limited_library_record():
    """Simple library record."""
    yield {
        '$schema': url_schema + '/libraries/library-v0.0.1.json',
        'pid': 'library_pid',
        'code': 'vsmvvs',
        'name': 'MV Sion',
        'address': 'Rue Pratifori',
        'email': 'info@mv.ch',
        'opening_hours': [
            {
                'day': 'monday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'tuesday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'wednesday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'thursday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'friday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'saturday',
                'is_open': False,
                'time': []
            },
            {
                'day': 'sunday',
                'is_open': False,
                'time': []
            }
        ]
    }


@pytest.yield_fixture()
def limited_location_record():
    """Simple location record."""
    yield {
        '$schema': url_schema + '/locations/location-v0.0.1.json',
        'pid': 'location_pid',
        'code': 'net-store-base',
        'name': 'Store Base',
        'is_pickup': True,
        'pickup_name': 'Store Base pickup',
    }


@pytest.yield_fixture()
def limited_item_record():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': 'item_pid',
        'barcode': '10000000000',
        'call_number': 'PA-41234',
        'location_pid': 'location_pid',
        'item_type_pid': 'item_type_pid',
        'item_status': 'on_shelf',
    }


@pytest.yield_fixture()
def limited_document_record():
    """Minimal document."""
    yield {
        '$schema': url_schema + '/documents/document-v0.0.1.json',
        'pid': 'document_pid',
        'title': 'RERO21 pour les nuls : les premiers pas',
        'type': 'book',
        'languages': [{'language': 'fre'}],
    }


@pytest.yield_fixture()
def limited_patron_simonetta():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': 'simonetta_pid',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'barcode': '2050124311',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type_pid': 'patron_type_pid',
        'library_pid': 'library_pid',
        'is_staff': True,
        'is_patron': True,
    }


@pytest.yield_fixture()
def limited_patron_philippe():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': 'philippe_pid',
        'first_name': 'Philippe',
        'last_name': 'Monnet',
        'street': 'Rue du Nord 7',
        'postal_code': '1950',
        'city': 'Sion',
        'barcode': 'reroils1',
        'birth_date': '2001-12-12',
        'email': 'reroilstest+philippe@gmail.com',
        'patron_type_pid': 'patron_type_pid',
        'library_pid': 'library_pid',
        'is_staff': True,
        'is_patron': True,
    }


@pytest.yield_fixture()
def limited_patron_type_record():
    """Patron Type minimal record."""
    yield {
        '$schema': url_schema + '/patrons_types/patron_type-v0.0.1.json',
        'pid': 'patron_type_pid',
        'name': 'Patron Type Name',
        'description': 'Patron Type Description',
        'organisation_pid': '1',
    }


@pytest.yield_fixture()
def limited_item_type_record():
    """Item Type minimal record."""
    yield {
        '$schema': url_schema + '/items_types/item_type-v0.0.1.json',
        'pid': 'item_type_pid',
        'name': 'Item Type Name',
        'description': 'Item Type Description',
        'organisation_pid': '1',
    }


@pytest.yield_fixture()
def all_resources_limited(
    db,
    limited_organisation_record,
    limited_library_record,
    limited_location_record,
    limited_item_record,
    limited_document_record,
    limited_item_type_record,
    limited_patron_simonetta,
    limited_patron_philippe,
    limited_patron_type_record,
    es_clear,
):
    """Minimal resources."""
    ItemType.create(
        limited_item_type_record, dbcommit=True, reindex=True, delete_pid=False
    )
    PatronType.create(
        limited_patron_type_record,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    library = LibraryWithLocations.create(
        limited_library_record, dbcommit=True, reindex=True, delete_pid=False
    )
    location = Location.create(
        limited_location_record, dbcommit=True, reindex=True, delete_pid=False
    )
    library.add_location(location, dbcommit=True, reindex=True)

    organisation = OrganisationWithLibraries.create(
        limited_organisation_record,
        dbcommit=True,
        reindex=True,
        delete_pid=False
    )
    organisation.add_library(library)

    simonetta = Patron.create(
        limited_patron_simonetta, dbcommit=True, reindex=True, delete_pid=False
    )
    philippe = Patron.create(
        limited_patron_philippe, dbcommit=True, reindex=True, delete_pid=False
    )

    doc = DocumentsWithItems.create(
        limited_document_record, dbcommit=True, reindex=True, delete_pid=False
    )
    item = Item.create(limited_item_record, delete_pid=False)
    doc.add_item(item, dbcommit=True, reindex=True)
    item.dbcommit(reindex=True)
    db.session.commit()
    yield doc, item, organisation, library, location, simonetta, philippe


@pytest.yield_fixture()
def limited_library_record_2():
    """Simple library record."""
    yield {
        '$schema': url_schema + '/libraries/library-v0.0.1.json',
        'pid': 'library_pid_2',
        'code': 'vsmvvs',
        'name': 'MV Martigny ',
        'address': 'ave de la gare',
        'email': 'info@artigny.ch',
        'opening_hours': [
            {
                'day': 'monday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'tuesday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'wednesday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'thursday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'friday',
                'is_open': True,
                'time': [
                    {
                        'start_time': '07:00',
                        'end_time': '19:00'
                    }
                ]
            },
            {
                'day': 'saturday',
                'is_open': False,
                'time': []
            },
            {
                'day': 'sunday',
                'is_open': False,
                'time': []
            }
        ]
    }


@pytest.yield_fixture()
def limited_location_record_2():
    """Simple location record."""
    yield {
        '$schema': url_schema + '/locations/location-v0.0.1.json',
        'pid': 'location_pid_2',
        'code': 'net-store-base 2',
        'name': 'Store Base 2',
        'is_pickup': True,
        'pickup_name': 'Store Base pickup 2',
    }


@pytest.yield_fixture()
def limited_item_record_2():
    """Simple item record with no transactions."""
    yield {
        '$schema': url_schema + '/items/item-v0.0.1.json',
        'pid': 'item_pid_2',
        'barcode': '20000000000',
        'call_number': 'CA-41234',
        'location_pid': 'location_pid_2',
        'item_type_pid': 'item_type_pid_2',
        'item_status': 'on_shelf',
    }


@pytest.yield_fixture()
def limited_document_record_2():
    """Minimal document."""
    yield {
        '$schema': url_schema + '/documents/document-v0.0.1.json',
        'pid': 'document_pid_2',
        'title': 'RERO21 pour les smarts',
        'type': 'book',
        'languages': [{'language': 'fre'}],
    }


@pytest.yield_fixture()
def limited_patron_simonetta_2():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': 'simonetta_pid_2',
        'first_name': 'Simonetta2',
        'last_name': 'Casalini2',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'barcode': '3050124311',
        'birth_date': '1967-06-07',
        'email': 'simolibri08@gmail.com',
        'phone': '+41324993585',
        'patron_type_pid': 'patron_type_pid_2',
        'library_pid': 'library_pid_2',
        'is_staff': True,
        'is_patron': True,
    }


@pytest.yield_fixture()
def limited_patron_philippe_2():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': 'philippe_pid_2',
        'first_name': 'Philippe2',
        'last_name': 'Monnet2',
        'street': 'Rue du Nord 8',
        'postal_code': '1950',
        'city': 'Sion',
        'barcode': 'reroils2',
        'birth_date': '2001-12-12',
        'email': 'reroilstest+philippe2@gmail.com',
        'patron_type_pid': 'patron_type_pid_2',
        'library_pid': 'library_pid_2',
        'is_staff': True,
        'is_patron': True,
    }


@pytest.yield_fixture()
def limited_patron_type_record_2():
    """Patron Type minimal record."""
    yield {
        '$schema': url_schema + '/patrons_types/patron_type-v0.0.1.json',
        'pid': 'patron_type_pid_2',
        'name': 'Patron Type Name 2',
        'description': 'Patron Type Description 2',
        'organisation_pid': '1',
    }


@pytest.yield_fixture()
def limited_item_type_record_2():
    """Item Type minimal record."""
    yield {
        '$schema': url_schema + '/items_types/item_type-v0.0.1.json',
        'pid': 'item_type_pid_2',
        'name': 'Item Type Name 2',
        'description': 'Item Type Description 2',
        'organisation_pid': '1',
    }


@pytest.yield_fixture()
def all_resources_limited_2(
    db,
    limited_organisation_record_2,
    limited_library_record_2,
    limited_location_record_2,
    limited_item_record_2,
    limited_document_record_2,
    limited_item_type_record_2,
    limited_patron_simonetta_2,
    limited_patron_philippe_2,
    limited_patron_type_record_2,
    es_clear,
):
    """Minimal resources."""
    ItemType.create(
        limited_item_type_record_2,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    PatronType.create(
        limited_patron_type_record_2,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    library = LibraryWithLocations.create(
        limited_library_record_2, dbcommit=True, reindex=True, delete_pid=False
    )
    location = Location.create(
        limited_location_record_2,
        dbcommit=True, reindex=True, delete_pid=False
    )
    library.add_location(location, dbcommit=True, reindex=True)

    organisation = OrganisationWithLibraries.create(
        limited_organisation_record_2,
        dbcommit=True,
        reindex=True,
        delete_pid=False
    )
    organisation.add_library(library)

    simonetta = Patron.create(
        limited_patron_simonetta_2,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    philippe = Patron.create(
        limited_patron_philippe_2,
        dbcommit=True, reindex=True, delete_pid=False
    )

    doc = DocumentsWithItems.create(
        limited_document_record_2,
        dbcommit=True, reindex=True, delete_pid=False
    )
    item = Item.create(limited_item_record_2, delete_pid=False)
    doc.add_item(item, dbcommit=True, reindex=True)
    item.dbcommit(reindex=True)
    db.session.commit()
    yield doc, item, organisation, library, location, simonetta, philippe


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
        'email': 'info@mv.ch',
        'opening_hours': [
            {
                'day': 'monday',
                'is_open': True,
                'times': [{'start_time': '07:00', 'end_time': '19:00'}]
            },
            {
                'day': 'tuesday',
                'is_open': True,
                'times': [{'start_time': '07:00', 'end_time': '19:00'}]
            },
            {
                'day': 'wednesday',
                'is_open': True,
                'times': [{'start_time': '07:00', 'end_time': '19:00'}]
            },
            {
                'day': 'thursday',
                'is_open': True,
                'times': [{'start_time': '07:00', 'end_time': '19:00'}]
            },
            {
                'day': 'friday',
                'is_open': True,
                'times': [{'start_time': '07:00', 'end_time': '19:00'}]
            },
            {
                'day': 'saturday',
                'is_open': False,
                'times': []
            },
            {
                'day': 'sunday',
                'is_open': False,
                'time': []
            }
        ],
    }


@pytest.yield_fixture()
def exception_dates():
    """Simple exception dates."""
    yield [
        {
            'end_date': '2019-01-06',
            'is_open': False,
            'start_date': '2018-12-22',
            'title': 'Vacances de Noël'
        },
        {
            'is_open': True,
            'start_date': '2018-12-15',
            'times': [{'end_time': '16:00', 'start_time': '10:00'}],
            'title': 'Samdi du livre'
        },
        {
            'is_open': False,
            'repeat': {
                'interval': 1,
                'period': 'yearly'
            },
            'start_date': '2019-08-01',
            'title': '1er août'
        }
    ]


@pytest.yield_fixture()
def minimal_location_record():
    """Simple location record."""
    yield {
        '$schema': url_schema + '/locations/location-v0.0.1.json',
        'pid': '1',
        'code': 'net-store-base',
        'name': 'Store Base',
    }


# @pytest.yield_fixture()
# def minimal_item_record():
#     """Simple item record."""
#     yield {
#         '$schema': url_schema + '/items/item-v0.0.1.json',
#         'pid': '1',
#         'barcode': '10000000000',
#         'call_number': 'PA-41234',
#         'location_pid': '1',
#         'item_type_pid': '1',
#         '_circulation': {
#             'holdings': [
#                 {
#                     'patron_barcode': '123456',
#                     'start_date': '2018-01-01',
#                     'end_date': '2018-02-01',
#                     'renewal_count': 0,
#                 },
#                 {
#                     'patron_barcode': '654321',
#                     'start_date': '2018-10-10',
#                     'end_date': '2018-11-10',
#                     'pickup_library_pid': '1',
#                 },
#             ],
#             'status': 'on_loan',
#         },
#     }


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
            'holdings': [
                {
                    'patron_barcode': '654321',
                    'start_date': '2018-10-10',
                    'end_date': '2018-11-10',
                    'pickup_library_pid': '1',
                }
            ],
            'status': 'on_shelf',
        },
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
        '_circulation': {'holdings': [], 'status': 'in_transit'},
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
        '_circulation': {'holdings': [], 'status': 'on_shelf'},
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
            'holdings': [
                {
                    'patron_barcode': '123456',
                    'start_date': '2018-01-01',
                    'end_date': '2018-02-01',
                    'renewal_count': 0,
                }
            ],
            'status': 'on_loan',
        },
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
        'patron_type_pid': '1',
    }


@pytest.yield_fixture()
def minimal_patron_type_record():
    """Patron Type minimal record."""
    yield {
        '$schema': url_schema + '/patrons_types/patron_type-v0.0.1.json',
        'pid': '1',
        'name': 'Patron Type Name',
        'description': 'Patron Type Description',
        'organisation_pid': '1',
    }


@pytest.yield_fixture()
def minimal_item_type_record():
    """Item Type minimal record."""
    yield {
        '$schema': url_schema + '/items_types/item_type-v0.0.1.json',
        'pid': '1',
        'name': 'Item Type Name',
        'description': 'Item Type Description',
        'organisation_pid': '1',
    }


@pytest.yield_fixture()
def create_minimal_resources(
    db,
    es,
    minimal_library_record,
    minimal_location_record,
    limited_item_record,
    minimal_document_record,
    minimal_item_type_record,
):
    """Minimal resources."""
    ItemType.create(minimal_item_type_record, dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True, reindex=True
    )
    location = Location.create(
        minimal_location_record, dbcommit=True, reindex=True
    )
    library.add_location(location)
    doc = DocumentsWithItems.create(
        minimal_document_record, dbcommit=True, reindex=True
    )
    item = Item.create(limited_item_record, dbcommit=True, reindex=True)
    doc.add_item(item, dbcommit=True, reindex=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf(
    db,
    minimal_library_record,
    minimal_location_record,
    item_record_on_shelf,
    minimal_document_record,
    minimal_item_type_record,
):
    """Minimal resources on_shelf."""
    ItemType.create(minimal_item_type_record, dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_on_shelf_req(
    db,
    minimal_library_record,
    minimal_location_record,
    item_record_on_shelf_requested,
    minimal_document_record,
    minimal_item_type_record,
):
    """Minimal resources on_shelf req."""
    ItemType.create(minimal_item_type_record, dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_shelf_requested, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_in_transit(
    db,
    minimal_library_record,
    minimal_location_record,
    item_record_in_transit,
    minimal_document_record,
    minimal_item_type_record,
):
    """Minimal resources in_transit."""
    ItemType.create(minimal_item_type_record, dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_in_transit, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location


@pytest.yield_fixture()
def create_minimal_resources_on_loan(
    db,
    minimal_library_record,
    minimal_location_record,
    item_record_on_loan,
    minimal_document_record,
    minimal_item_type_record,
):
    """Minimal resources on_loan."""
    ItemType.create(minimal_item_type_record, dbcommit=True, reindex=True)
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    library.add_location(location)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    item = Item.create({})
    item.update(item_record_on_loan, dbcommit=True)
    doc.add_item(item, dbcommit=True)
    db.session.commit()
    yield doc, item, library, location
