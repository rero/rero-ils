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

"""Click command-line interface for item record management."""

from __future__ import absolute_import, print_function

import json
import random
from datetime import datetime, timedelta, timezone

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_circulation.api import get_loan_for_item
from invenio_indexer.api import RecordIndexer
from werkzeug.local import LocalProxy

from rero_ils.modules.items.utils import commit_item
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.locations.api import Location

from ..documents_items.api import DocumentsSearch, DocumentsWithItems
from ..items.api import Item, ItemStatus
from ..items_types.api import ItemType
from ..libraries_locations.api import LibraryWithLocations
from ..loans.api import get_request_by_item_pid_by_patron_pid
from ..loans.utils import is_item_available_for_checkout
from ..patrons.api import Patron, PatronsSearch

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('createcirctransactions')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def create_circ_transactions(infile, verbose):
    """Create circulation transactions.

    infile: Json transactions file
    """
    click.secho('Create circulation transactions:', fg='green')
    data = json.load(infile)
    for patron_data in data:
        barcode = patron_data.get('barcode')
        if barcode is None:
            click.secho('\tPatron barcode is missing!', fg='red')
        else:
            loans = patron_data.get('loans', {})
            requests = patron_data.get('requests', {})

            for transaction in range(loans.get('active', 0)):
                item_barcode = create_loan(barcode, 'active')
                print_message(barcode, item_barcode, 'active')

            for transaction in range(loans.get('overdue', 0)):
                item_barcode = create_loan(barcode, 'overdue')
                print_message(barcode, item_barcode, 'overdue')

            for transaction in range(loans.get('extended', 0)):
                item_barcode = create_loan(barcode, 'extended')
                print_message(barcode, item_barcode, 'extended')

            for transaction in range(loans.get('requested_by_others', 0)):
                item_barcode = create_loan(barcode, 'requested_by_others')
                print_message(barcode, item_barcode, 'requested_by_others')

            for transaction in range(requests.get('requests', 0)):
                item_barcode = create_request(barcode, 'requests')
                print_message(barcode, item_barcode, 'requests')

            for transaction in range(requests.get('rank_1', 0)):
                item_barcode = create_request(barcode, 'rank_1')
                print_message(barcode, item_barcode, 'rank_1')

            for transaction in range(requests.get('rank_2', 0)):
                item_barcode = create_request(barcode, 'rank_2')
                print_message(barcode, item_barcode, 'rank_2')


def print_message(barcode, item_barcode, transaction_type):
    """Print confirmation message."""
    click.echo(
        '\t {transaction_type} created for patron {barcode} and item \
         {item_barcode}'.format(
            transaction_type=transaction_type,
            barcode=barcode, item_barcode=item_barcode
        )
    )


def get_one_library():
    """Find a qualified library."""
    libraries_pids = Library.get_all_pids()
    return random.choice(libraries_pids)


def get_one_location():
    """Find a qualified location."""
    locations_pids = Location.get_all_pids()
    return random.choice(locations_pids)


def get_one_pickup_location(item_pid):
    """Find a qualified pickup location."""
    location_pid = Item.get_record_by_pid(item_pid)['location_pid']
    location = Location.get_record_by_pid(location_pid)
    library = LibraryWithLocations.get_library_by_locationid(location.id)
    locations = library.pickup_locations
    return locations[0]['pid']


def get_loan_dates(transaction_type, item):
    """Get loan dates."""
    if item.get('item_type_pid') == '2':
        duration = 15
    else:
        duration = 30
    today = datetime.today()
    start_today = datetime.strftime(today, '%Y-%m-%d')
    end_date_duration = today + timedelta(duration)
    start_date = start_today
    end_date = datetime.strftime(end_date_duration, '%Y-%m-%d')
    if transaction_type == 'overdue':
        today_overdue = datetime.today() - timedelta(50)
        start_today_overdue = datetime.strftime(today_overdue, '%Y-%m-%d')
        start_date = start_today_overdue
        e_end_date = today_overdue + timedelta(duration)
        end_date = datetime.strftime(e_end_date, '%Y-%m-%d')
    return start_date, end_date


def get_one_patron(exclude_this_barcode):
    """Find a qualified patron other than exclude_this_barcode."""
    patrons = PatronsSearch().filter('term', **{
        'is_patron': True}).source().scan()
    for patron in patrons:
        if patron.barcode != exclude_this_barcode:
            return Patron.get_patron_by_barcode(barcode=patron.barcode)


def get_one_staff_user():
    """Find a qualified staff user."""
    patrons = PatronsSearch().filter('term', **{
        'is_staff': True}).source().scan()
    for patron in patrons:
        return Patron.get_record_by_pid(patron.pid)


def get_one_user_data():
    """Find a qualified user data."""
    user = get_one_staff_user().dumps()
    user_pid = user.get('pid')
    user_location = user.get('circulation_location_pid')
    return user_pid, user_location


def create_loan(barcode, transaction_type):
    """Create loans transactions."""
    item = get_one_item(barcode, transaction_type)
    start_date, end_date = get_loan_dates(transaction_type, item)
    patron = Patron.get_patron_by_barcode(barcode=barcode)
    transaction_date = datetime.now(timezone.utc).isoformat()
    user_pid, user_location = get_one_user_data()
    item.loan_item(
        patron_pid=patron.pid,
        transaction_user_pid=user_pid,
        transaction_location_pid=user_location,
        transaction_date=transaction_date,
        document_pid=DocumentsWithItems.document_retriever(
            item_pid=item.pid),
        item_pid=item.pid,
    )
    if transaction_type == 'extended':
        loan = get_loan_for_item(item.pid)
        loan_pid = loan['loan_pid']
        user_pid, user_location = get_one_user_data()
        item.extend_loan(
            loan_pid=loan_pid,
            patron_pid=patron.pid,
            transaction_location_pid=user_location,
            transaction_user_pid=user_pid,
            transaction_date=transaction_date,
            document_pid=DocumentsWithItems.document_retriever(
                item_pid=item.pid),
            item_pid=item.pid,
        )
    if transaction_type == 'requested_by_others':
        requested_patron = get_one_patron(barcode)
        user_pid, user_location = get_one_user_data()
        item.request_item(
            patron_pid=requested_patron.pid,
            transaction_location_pid=user_location,
            transaction_user_pid=user_pid,
            transaction_date=transaction_date,
            pickup_location_pid=get_one_pickup_location(item.pid),
            document_pid=DocumentsWithItems.document_retriever(
                item_pid=item.pid),
        )
    commit_item(item)
    RecordIndexer().client.indices.flush()
    return item['barcode']


def create_request(barcode, transaction_type):
    """Create request transactions."""
    item = get_one_item(barcode, transaction_type)
    rank_1_patron = get_one_patron(barcode)
    patron = Patron.get_patron_by_barcode(barcode)
    if transaction_type == 'rank_2':
        transaction_date = (
            datetime.now(timezone.utc) - timedelta(2)).isoformat()
        user_pid, user_location = get_one_user_data()
        item.request_item(
            patron_pid=rank_1_patron.pid,
            transaction_location_pid=user_location,
            transaction_user_pid=user_pid,
            transaction_date=transaction_date,
            pickup_location_pid=get_one_pickup_location(item.pid),
            document_pid=DocumentsWithItems.document_retriever(
                item_pid=item.pid),
        )
    transaction_date = datetime.now(timezone.utc).isoformat()
    user_pid, user_location = get_one_user_data()
    item.request_item(
        patron_pid=patron.pid,
        transaction_location_pid=user_location,
        transaction_user_pid=user_pid,
        transaction_date=transaction_date,
        pickup_location_pid=get_one_pickup_location(item.pid),
        document_pid=DocumentsWithItems.document_retriever(
            item_pid=item.pid),
    )
    commit_item(item)
    RecordIndexer().client.indices.flush()
    return item['barcode']


def get_one_item(barcode, transaction_type):
    """Find a qualified item."""
    document_on_shelf = (
        DocumentsSearch()
        .filter('term', **{'itemslist.item_status': 'on_shelf'})
        .source(includes=['itemslist.*'])
        .scan()
    )
    patron = Patron.get_patron_by_barcode(barcode=barcode)
    for document in document_on_shelf:
        for items in document['itemslist']:
            item = items.to_dict()
            if is_item_available_for_checkout(item.get('pid')):
                if (
                    transaction_type
                    in (
                        'active',
                        'overdue',
                        'extended',
                        'requested_by_others') and
                    item['item_status'] == ItemStatus.ON_SHELF and
                    item['item_type_pid'] != ItemType.get_pid_by_name(
                        'on-site') and
                    item['requests_count'] == 0
                ):
                    return Item.get_record_by_pid(pid=item['pid'])
                if (
                    transaction_type == 'requests' and
                    item['item_status'] != ItemStatus.MISSING and
                    item['requests_count'] < 3 and
                    patron_requested(item['pid'], patron.pid) is False
                ):
                    return Item.get_record_by_pid(pid=item['pid'])
                if (
                    transaction_type in ('rank_1', 'rank_2') and
                    item['item_status'] != ItemStatus.MISSING and
                    item['requests_count'] == 0
                ):
                    return Item.get_record_by_pid(pid=item['pid'])


def patron_requested(item_pid, patron_pid):
    """Check if the item is requested by a given patron."""
    request = get_request_by_item_pid_by_patron_pid(
        item_pid, patron_pid
    )
    if request:
        return True
    return False
