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

"""Click command-line interface for item record management."""

from __future__ import absolute_import, print_function

import json
import random
from datetime import datetime, timedelta

import click
import pytz
from flask import current_app
from flask.cli import with_appcontext
from invenio_indexer.api import RecordIndexer
from werkzeug.local import LocalProxy

from reroils_app.modules.items.utils import commit_item
from reroils_app.modules.members.api import Member

from ..documents_items.api import DocumentsSearch
from ..items.api import Item, ItemStatus
from ..patrons.api import Patron, PatronsSearch

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('createcirctransactions')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', 'Json transactions file', type=click.File('r'))
@with_appcontext
def create_circ_transactions(infile, verbose):
    """Create circulation transactions."""
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
    click.echo('\t {0} created for patron {1} and item {2}'
               .format(transaction_type, barcode, item_barcode))


def get_one_member():
    """Find a qualified member."""
    members_pids = Member.get_all_pids()
    return random.choice(members_pids)


def get_loan_dates(transaction_type, item):
    """Get loan dates."""
    today = datetime.today()
    start_today = datetime.strftime(today, '%Y-%m-%d')
    end_date_duration = today + timedelta(item.duration)
    start_date = start_today
    end_date = datetime.strftime(end_date_duration, '%Y-%m-%d')
    if transaction_type == 'overdue':
        today_overdue = datetime.today() - timedelta(50)
        start_today_overdue = datetime.strftime(today_overdue, '%Y-%m-%d')
        start_date = start_today_overdue
        e_end_date = today_overdue + timedelta(item.duration)
        end_date = datetime.strftime(e_end_date, '%Y-%m-%d')
    return start_date, end_date


def get_one_patron(input_barcode):
    """Find a qualified patron."""
    patrons = list(PatronsSearch().filter(
        "term", **{"is_patron": True}
    ).source().scan())
    for patron in patrons:
        record = patron.to_dict()
        barcode = record.get('barcode')
        if barcode != input_barcode:
            return Patron.get_patron_by_barcode(barcode=barcode)


def create_loan(barcode, transaction_type):
    """Create loans transactions."""
    item = get_one_item(barcode, transaction_type)
    start_date, end_date = get_loan_dates(transaction_type, item)
    item.loan_item(
        patron_barcode=barcode,
        start_date=start_date,
        end_date=end_date
    )
    if transaction_type == 'extended':
        item.extend_loan(
            patron_barcode=barcode
        )
    if transaction_type == 'requested_by_others':
        requested_patron = get_one_patron(barcode)
        request_datetime = pytz.utc.localize(datetime.now()).isoformat()
        item.request_item(
            patron_barcode=requested_patron['barcode'],
            pickup_member_pid=get_one_member(),
            request_datetime=request_datetime
        )
    commit_item(item)
    RecordIndexer().client.indices.flush()
    return item['barcode']


def create_request(barcode, transaction_type):
    """Create request transactions."""
    item = get_one_item(barcode, transaction_type)
    if transaction_type == 'rank_2':
        patron = get_one_patron(barcode)
        first_barcode = patron['barcode']
        request_datetime = pytz.utc.localize(
            datetime.now() - timedelta(2)).isoformat()
        item.request_item(
            patron_barcode=first_barcode,
            pickup_member_pid=get_one_member(),
            request_datetime=request_datetime
        )
    request_datetime = pytz.utc.localize(datetime.now()).isoformat()
    item.request_item(
        patron_barcode=barcode,
        pickup_member_pid=get_one_member(),
        request_datetime=request_datetime
    )
    commit_item(item)
    RecordIndexer().client.indices.flush()
    return item['barcode']


def get_one_item(barcode, transaction_type):
    """Find a qualified item."""
    document_on_shelf = DocumentsSearch(
    ).filter(
        "term", **{"itemslist._circulation.status": "on_shelf"}
    ).source(includes=['itemslist.*']).scan()
    for document in document_on_shelf:
        for items in document['itemslist']:
            item = items.to_dict()
            if (
                transaction_type in (
                    'active', 'overdue', 'extended', 'requested_by_others') and
                item['_circulation']['status'] == ItemStatus.ON_SHELF and
                item['item_type'] != 'on_site_consultation' and
                item['requests_count'] == 0
            ):
                return Item.get_record_by_pid(pid=item['pid'])
            if (
                    transaction_type == 'requests' and
                    item['_circulation']['status'] != ItemStatus.MISSING and
                    item['requests_count'] < 3 and
                    patron_requested(item, barcode) is False
            ):
                return Item.get_record_by_pid(pid=item['pid'])
            if (
                    transaction_type in ('rank_1', 'rank_2') and
                    item['_circulation']['status'] != ItemStatus.MISSING and
                    item['requests_count'] == 0
            ):
                    return Item.get_record_by_pid(pid=item['pid'])


def patron_requested(item, patron_barcode):
    """Check if the item is requested by a given patron."""
    for holding in item.get('_circulation', {}).get('holdings', 0):
        if holding and holding.get('patron_barcode'):
            if holding['patron_barcode'] == patron_barcode:
                return True
    return False
