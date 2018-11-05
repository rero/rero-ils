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

import copy
import datetime

import pytest

from rero_ils.modules.items.api import Item, ItemStatus
from rero_ils.modules.libraries_locations.api import LibraryWithLocations
from rero_ils.modules.locations.api import Location


def test_extend_item(db, create_minimal_resources_on_loan,
                     minimal_patron_only_record,
                     minimal_patron_record):

    doc, item, library, location = create_minimal_resources_on_loan
    assert library
    assert item
    assert location
    assert doc
    assert library.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_no_req = copy.deepcopy(item)
    assert item_no_req.status == ItemStatus.ON_LOAN
    assert item_no_req.number_of_item_requests() == 0
    item_no_req.extend_loan(requested_end_date='2018-02-01')
    end_date = item_no_req['_circulation']['holdings'][0]['end_date']
    assert end_date == '2018-02-01'
    item_no_req.extend_loan()
    current_date = datetime.date.today()
    end_date = (current_date + datetime.timedelta(days=30)).isoformat()
    assert item_no_req['_circulation']['holdings'][0]['end_date'] == end_date
    item_no_req.extend_loan()
    current_date = datetime.date.today()
    end_date = (current_date + datetime.timedelta(days=30)).isoformat()
    assert item_no_req['_circulation']['holdings'][0]['end_date'] == end_date


def test_return_item(app, db, create_minimal_resources_on_loan,
                     minimal_patron_only_record,
                     minimal_patron_record):

    doc, item, library, location = create_minimal_resources_on_loan
    assert library
    assert item
    assert location
    assert doc
    assert library.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_no_req = copy.deepcopy(item)
    assert item_no_req.status == ItemStatus.ON_LOAN
    assert item_no_req.number_of_item_requests() == 0
    data_no_req = item_no_req.dumps()
    assert data_no_req.get('library_pid') == '1'
    item_no_req.return_item(transaction_library_pid='1')
    db.session.commit()
    assert item_no_req.status == ItemStatus.ON_SHELF

    item_req = copy.deepcopy(item)
    assert item_req.status == ItemStatus.ON_LOAN
    assert item_req.number_of_item_requests() == 0
    item_req.request_item(
        patron_barcode=patron_barcode,
        pickup_library_pid='1'
    )
    db.session.commit()
    assert item_req.number_of_item_requests() == 1
    data_req = item_req.dumps()
    assert data_req.get('library_pid') == '1'

    holding_req = item_req.get('_circulation').get('holdings')[1]
    assert holding_req['pickup_library_pid'] == '1'
    item_req.return_item(transaction_library_pid='1')
    db.session.commit()
    assert item_req.status == ItemStatus.AT_DESK

    # item is requested and pickup <> transaction library

    item_req_ext = copy.deepcopy(item)
    assert item_req_ext.status == ItemStatus.ON_LOAN
    assert item_req_ext.number_of_item_requests() == 0
    item_req_ext.request_item(
        patron_barcode=patron_barcode,
        pickup_library_pid='1'
    )
    db.session.commit()
    assert item_req_ext.number_of_item_requests() == 1
    data_req_ext = item_req_ext.dumps()
    assert data_req_ext.get('library_pid') == '1'

    item_req_ext.get('_circulation').get('holdings')[1]
    assert holding_req['pickup_library_pid'] == '1'
    item_req_ext.return_item(transaction_library_pid='2')
    db.session.commit()
    assert item_req_ext.status == ItemStatus.IN_TRANSIT


def test_validate_item(app, db, create_minimal_resources_on_shelf_req,
                       minimal_patron_only_record,
                       minimal_patron_record):

    doc, item, library, location = create_minimal_resources_on_shelf_req
    assert library
    assert item
    assert location
    assert doc
    assert library.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_req = copy.deepcopy(item)
    assert item_req.status == ItemStatus.ON_SHELF
    assert item_req.number_of_item_requests() == 1
    data_req = item_req.dumps()
    assert data_req.get('library_pid') == '1'
    holding = item_req.get('_circulation').get('holdings')[0]
    assert holding['pickup_library_pid'] == '1'
    item_req['_circulation']['holdings'][0]['pickup_library_pid'] = '2'
    holding = item_req.get('_circulation').get('holdings')[0]
    assert holding['pickup_library_pid'] == '2'
    item_req.validate_item_request()
    db.session.commit()
    assert item_req.status == ItemStatus.IN_TRANSIT

    item_req_intern = copy.deepcopy(item)
    assert item_req_intern.status == ItemStatus.ON_SHELF
    assert item_req_intern.number_of_item_requests() == 1
    data_req = item_req_intern.dumps()
    assert data_req.get('library_pid') == '1'
    holding = item_req_intern.get('_circulation').get('holdings')[0]
    assert holding['pickup_library_pid'] == '1'
    item_req_intern.validate_item_request()
    db.session.commit()
    assert item_req_intern.status == ItemStatus.AT_DESK


@pytest.mark.skip(reason="will be changet with invenio_circulation")
def test_receive_item(app, db, create_minimal_resources_in_transit,
                      minimal_patron_only_record,
                      minimal_patron_record):

    doc, item, library, location = create_minimal_resources_in_transit
    assert library
    assert item
    assert location
    assert doc
    assert library.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_in_transit = copy.deepcopy(item)
    assert item_in_transit.status == ItemStatus.IN_TRANSIT
    assert item_in_transit.number_of_item_requests() == 0
    data_in_transit = item_in_transit.dumps()
    assert data_in_transit.get('library_pid') == '1'
    item_in_transit.receive_item(transaction_library_pid='1')
    db.session.commit()
    assert item_in_transit.status == ItemStatus.ON_SHELF

    item_in_transit_req = copy.deepcopy(item)
    assert item_in_transit_req.status == ItemStatus.IN_TRANSIT
    assert item_in_transit_req.number_of_item_requests() == 0
    item_in_transit_req.request_item(
        patron_barcode=patron_barcode,
        pickup_library_pid='1'
    )
    db.session.commit()
    assert item_in_transit_req.status == ItemStatus.IN_TRANSIT
    assert item_in_transit_req.number_of_item_requests() == 1
    holding = item_in_transit_req.get('_circulation').get('holdings')[0]
    assert holding['pickup_library_pid'] == '1'
    item_in_transit_req.receive_item(transaction_library_pid='1')
    db.session.commit()
    assert item_in_transit_req.status == ItemStatus.AT_DESK

    item_in_transit_ext = copy.deepcopy(item)
    assert item_in_transit_ext.status == ItemStatus.IN_TRANSIT
    assert item_in_transit_ext.number_of_item_requests() == 0
    data_in_transit_ext = item_in_transit_ext.dumps()
    assert data_in_transit_ext.get('library_pid') == '1'
    item_in_transit_ext.receive_item(transaction_library_pid='2')
    db.session.commit()
    assert item_in_transit_ext.status == ItemStatus.IN_TRANSIT


def test_request_item(db, create_minimal_resources_on_shelf,
                      minimal_patron_only_record,
                      minimal_patron_record):

    doc, item, library, location = create_minimal_resources_on_shelf
    assert library
    assert item
    assert location
    assert doc
    assert library.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_on_shelf = copy.deepcopy(item)
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.number_of_item_requests() == 0
    item_on_shelf.request_item(
        patron_barcode=patron_barcode,
        pickup_library_pid='1'
    )
    db.session.commit()
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.number_of_item_requests() == 1

    patron_barcode_2 = minimal_patron_record['barcode']
    assert patron_barcode_2

    assert item_on_shelf.number_of_item_requests() == 1
    item_on_shelf.request_item(
        patron_barcode=patron_barcode_2,
        pickup_library_pid='1'
    )
    db.session.commit()
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.number_of_item_requests() == 2


def test_loan_item(db, create_minimal_resources_on_shelf,
                   minimal_patron_only_record):

    doc, item, library, location = create_minimal_resources_on_shelf
    assert library
    assert item
    assert location
    assert doc
    assert doc.available
    assert library.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_on_shelf = copy.deepcopy(item)
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.available
    item_on_shelf.loan_item(patron_barcode=patron_barcode)
    db.session.commit()
    assert item_on_shelf.status == ItemStatus.ON_LOAN
    assert not item_on_shelf.available

    item_at_desk = copy.deepcopy(item)
    assert item_at_desk.status == ItemStatus.ON_SHELF
    item_at_desk['_circulation']['status'] = ItemStatus.AT_DESK
    assert item_at_desk.status == ItemStatus.AT_DESK
    assert not item_at_desk.available
    item_at_desk.loan_item(patron_barcode=patron_barcode)
    db.session.commit()
    assert item_at_desk.status == ItemStatus.ON_LOAN


def test_nb_item_requests(db, minimal_item_record, minimal_patron_only_record):
    """Test number of item requests."""
    assert minimal_patron_only_record['barcode']
    patron_barcode = minimal_patron_only_record['barcode']
    item = Item.create({})
    item.update(minimal_item_record, dbcommit=True)
    item.request_item(patron_barcode=patron_barcode)
    tr_barcode = item['_circulation']['holdings'][2]['patron_barcode']
    assert tr_barcode == patron_barcode
    number_requests = item.number_of_item_requests()
    assert number_requests == 2


def test_library_name(db, minimal_library_record, minimal_item_record,
                      minimal_location_record):
    """Test library names."""
    library = LibraryWithLocations.create(
        minimal_library_record, dbcommit=True
    )
    assert library
    location = Location.create(minimal_location_record, dbcommit=True)
    assert location
    library.add_location(location, dbcommit=True)
    assert library.locations
    item = Item.create({})
    item.update(minimal_item_record, dbcommit=True)
    assert item
    data = item.dumps()
    assert data.get('library_pid') == '1'
    assert data.get('library_name') == 'MV Sion'
    holding = data.get('_circulation').get('holdings')[1]
    assert holding['pickup_library_name'] == 'MV Sion'
