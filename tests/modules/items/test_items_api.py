# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
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

import mock

from reroils_app.modules.items.api import Item, ItemStatus
from reroils_app.modules.locations.api import Location
from reroils_app.modules.members_locations.api import MemberWithLocations


def test_extend_item(db, create_minimal_resources_on_loan,
                     minimal_patron_only_record,
                     minimal_patron_record):

    doc, item, member, location = create_minimal_resources_on_loan
    assert member
    assert item
    assert location
    assert doc
    assert member.locations
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


@mock.patch('reroils_app.modules.patrons.listener.func_item_at_desk')
def test_return_item(func_item_at_desk,
                     db, create_minimal_resources_on_loan,
                     minimal_patron_only_record,
                     minimal_patron_record):

    doc, item, member, location = create_minimal_resources_on_loan
    assert member
    assert item
    assert location
    assert doc
    assert member.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_no_req = copy.deepcopy(item)
    assert item_no_req.status == ItemStatus.ON_LOAN
    assert item_no_req.number_of_item_requests() == 0
    data_no_req = item_no_req.dumps()
    assert data_no_req.get('member_pid') == '1'
    item_no_req.return_item(transaction_member_pid='1')
    db.session.commit()
    assert item_no_req.status == ItemStatus.ON_SHELF

    item_req = copy.deepcopy(item)
    assert item_req.status == ItemStatus.ON_LOAN
    assert item_req.number_of_item_requests() == 0
    item_req.request_item(
        patron_barcode=patron_barcode,
        pickup_member_pid='1'
    )
    db.session.commit()
    assert item_req.number_of_item_requests() == 1
    data_req = item_req.dumps()
    assert data_req.get('member_pid') == '1'

    holding_req = item_req.get('_circulation').get('holdings')[1]
    assert holding_req['pickup_member_pid'] == '1'
    item_req.return_item(transaction_member_pid='1')
    db.session.commit()
    assert item_req.status == ItemStatus.AT_DESK

    # item is requested and pickup <> transaction member

    item_req_ext = copy.deepcopy(item)
    assert item_req_ext.status == ItemStatus.ON_LOAN
    assert item_req_ext.number_of_item_requests() == 0
    item_req_ext.request_item(
        patron_barcode=patron_barcode,
        pickup_member_pid='1'
    )
    db.session.commit()
    assert item_req_ext.number_of_item_requests() == 1
    data_req_ext = item_req_ext.dumps()
    assert data_req_ext.get('member_pid') == '1'

    holding_req_ext = item_req_ext.get('_circulation').get('holdings')[1]
    assert holding_req['pickup_member_pid'] == '1'
    item_req_ext.return_item(transaction_member_pid='2')
    db.session.commit()
    assert item_req_ext.status == ItemStatus.IN_TRANSIT


@mock.patch('reroils_app.modules.patrons.listener.func_item_at_desk')
def test_validate_item(func_item_at_desk,
                       db, create_minimal_resources_on_shelf_req,
                       minimal_patron_only_record,
                       minimal_patron_record):

    doc, item, member, location = create_minimal_resources_on_shelf_req
    assert member
    assert item
    assert location
    assert doc
    assert member.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_req = copy.deepcopy(item)
    assert item_req.status == ItemStatus.ON_SHELF
    assert item_req.number_of_item_requests() == 1
    data_req = item_req.dumps()
    assert data_req.get('member_pid') == '1'
    holding = item_req.get('_circulation').get('holdings')[0]
    assert holding['pickup_member_pid'] == '1'
    item_req['_circulation']['holdings'][0]['pickup_member_pid'] = '2'
    holding = item_req.get('_circulation').get('holdings')[0]
    assert holding['pickup_member_pid'] == '2'
    item_req.validate_item_request()
    db.session.commit()
    assert item_req.status == ItemStatus.IN_TRANSIT

    item_req_intern = copy.deepcopy(item)
    assert item_req_intern.status == ItemStatus.ON_SHELF
    assert item_req_intern.number_of_item_requests() == 1
    data_req = item_req_intern.dumps()
    assert data_req.get('member_pid') == '1'
    holding = item_req_intern.get('_circulation').get('holdings')[0]
    assert holding['pickup_member_pid'] == '1'
    item_req_intern.validate_item_request()
    db.session.commit()
    assert item_req_intern.status == ItemStatus.AT_DESK


@mock.patch('reroils_app.modules.patrons.listener.func_item_at_desk')
def test_receive_item(func_item_at_desk,
                      db, create_minimal_resources_in_transit,
                      minimal_patron_only_record,
                      minimal_patron_record):

    doc, item, member, location = create_minimal_resources_in_transit
    assert member
    assert item
    assert location
    assert doc
    assert member.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_in_transit = copy.deepcopy(item)
    assert item_in_transit.status == ItemStatus.IN_TRANSIT
    assert item_in_transit.number_of_item_requests() == 0
    data_in_transit = item_in_transit.dumps()
    assert data_in_transit.get('member_pid') == '1'
    item_in_transit.receive_item(transaction_member_pid='1')
    db.session.commit()
    assert item_in_transit.status == ItemStatus.ON_SHELF

    item_in_transit_req = copy.deepcopy(item)
    assert item_in_transit_req.status == ItemStatus.IN_TRANSIT
    assert item_in_transit_req.number_of_item_requests() == 0
    item_in_transit_req.request_item(
        patron_barcode=patron_barcode,
        pickup_member_pid='1'
    )
    db.session.commit()
    assert item_in_transit_req.status == ItemStatus.IN_TRANSIT
    assert item_in_transit_req.number_of_item_requests() == 1
    holding = item_in_transit_req.get('_circulation').get('holdings')[0]
    assert holding['pickup_member_pid'] == '1'
    item_in_transit_req.receive_item(transaction_member_pid='1')
    db.session.commit()
    assert item_in_transit_req.status == ItemStatus.AT_DESK

    item_in_transit_ext = copy.deepcopy(item)
    assert item_in_transit_ext.status == ItemStatus.IN_TRANSIT
    assert item_in_transit_ext.number_of_item_requests() == 0
    data_in_transit_ext = item_in_transit_ext.dumps()
    assert data_in_transit_ext.get('member_pid') == '1'
    item_in_transit_ext.receive_item(transaction_member_pid='2')
    db.session.commit()
    assert item_in_transit_ext.status == ItemStatus.IN_TRANSIT


def test_request_item(db, create_minimal_resources_on_shelf,
                      minimal_patron_only_record,
                      minimal_patron_record):

    doc, item, member, location = create_minimal_resources_on_shelf
    assert member
    assert item
    assert location
    assert doc
    assert member.locations
    patron_barcode = minimal_patron_only_record['barcode']
    assert patron_barcode

    item_on_shelf = copy.deepcopy(item)
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.number_of_item_requests() == 0
    item_on_shelf.request_item(
        patron_barcode=patron_barcode,
        pickup_member_pid='1'
    )
    db.session.commit()
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.number_of_item_requests() == 1

    patron_barcode_2 = minimal_patron_record['barcode']
    assert patron_barcode_2

    assert item_on_shelf.number_of_item_requests() == 1
    item_on_shelf.request_item(
        patron_barcode=patron_barcode_2,
        pickup_member_pid='1'
    )
    db.session.commit()
    assert item_on_shelf.status == ItemStatus.ON_SHELF
    assert item_on_shelf.number_of_item_requests() == 2


def test_loan_item(db, create_minimal_resources_on_shelf,
                   minimal_patron_only_record):

    doc, item, member, location = create_minimal_resources_on_shelf
    assert member
    assert item
    assert location
    assert doc
    assert doc.available
    assert member.locations
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


def test_member_name(db, minimal_member_record, minimal_item_record,
                     minimal_location_record):
    """Test member names."""
    member = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    assert member
    location = Location.create(minimal_location_record, dbcommit=True)
    assert location
    member.add_location(location, dbcommit=True)
    assert member.locations
    item = Item.create({})
    item.update(minimal_item_record, dbcommit=True)
    assert item
    data = item.dumps()
    assert data.get('member_pid') == '1'
    assert data.get('member_name') == 'MV Sion'
    holding = data.get('_circulation').get('holdings')[1]
    assert holding['pickup_member_name'] == 'MV Sion'
