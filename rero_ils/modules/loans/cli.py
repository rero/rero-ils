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

"""Click command-line interface for item record management."""

from __future__ import absolute_import, print_function

import json
import random
from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext
from invenio_circulation.api import get_loan_for_item

from ..circ_policies.api import CircPolicy
from ..item_types.api import ItemType
from ..items.api import Item, ItemsSearch, ItemStatus
from ..libraries.api import Library
from ..locations.api import Location
from ..patron_types.api import PatronType
from ..patrons.api import Patron, PatronsSearch


@click.command('create_loans')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def create_loans(infile, verbose):
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
            patron_type_pid = Patron.get_patron_by_barcode(
                barcode).patron_type_pid
            loanable_items = get_loanable_items(patron_type_pid)

            for transaction in range(loans.get('active', 0)):
                item_barcode = create_loan(barcode, 'active', loanable_items)
                print_message(barcode, item_barcode, 'active')

            for transaction in range(loans.get('overdue', 0)):
                item_barcode = create_loan(barcode, 'overdue', loanable_items)
                print_message(barcode, item_barcode, 'overdue')

            for transaction in range(loans.get('extended', 0)):
                item_barcode = create_loan(barcode, 'extended', loanable_items)
                print_message(barcode, item_barcode, 'extended')

            for transaction in range(loans.get('requested_by_others', 0)):
                item_barcode = create_loan(
                    barcode, 'requested_by_others', loanable_items)
                print_message(barcode, item_barcode, 'requested_by_others')

            for transaction in range(requests.get('requests', 0)):
                item_barcode = create_request(
                    barcode, 'requests', loanable_items)
                print_message(barcode, item_barcode, 'requests')

            for transaction in range(requests.get('rank_1', 0)):
                item_barcode = create_request(
                    barcode, 'rank_1', loanable_items)
                print_message(barcode, item_barcode, 'rank_1')

            for transaction in range(requests.get('rank_2', 0)):
                item_barcode = create_request(
                    barcode, 'rank_2', loanable_items)
                print_message(barcode, item_barcode, 'rank_2')


def print_message(barcode, item_barcode, transaction_type):
    """Print confirmation message."""
    click.echo(
        (
            '\t'
            '{transaction_type} created for patron {barcode} '
            'and item {item_barcode}'
        ).format(
            transaction_type=transaction_type,
            barcode=barcode, item_barcode=item_barcode
        )
    )


def create_loan(barcode, transaction_type, loanable_items):
    """Create loans transactions."""
    item = next(loanable_items)
    patron = Patron.get_patron_by_barcode(barcode=barcode)
    start_date, end_date = get_loan_dates(transaction_type, item, patron)
    transaction_date = datetime.now(timezone.utc).isoformat()
    user_pid, user_location = get_random_librarian_and_transaction_location(
        patron)
    item.checkout(
        patron_pid=patron.pid,
        transaction_user_pid=user_pid,
        transaction_location_pid=user_location,
        transaction_date=transaction_date,
        document_pid=item.replace_refs()['document']['pid'],
        item_pid=item.pid,
    )
    if transaction_type == 'extended':
        loan = get_loan_for_item(item.pid)
        loan_pid = loan.get('pid')
        user_pid, user_location = \
            get_random_librarian_and_transaction_location(patron)
        item.extend_loan(
            pid=loan_pid,
            patron_pid=patron.pid,
            transaction_location_pid=user_location,
            transaction_user_pid=user_pid,
            transaction_date=transaction_date,
            document_pid=item.replace_refs()['document']['pid'],
            item_pid=item.pid,
        )
    if transaction_type == 'requested_by_others':
        requested_patron = get_random_patron(barcode)
        user_pid, user_location = \
            get_random_librarian_and_transaction_location(patron)
        circ_policy = CircPolicy.provide_circ_policy(
                item.library_pid,
                requested_patron.patron_type_pid,
                item.item_type_pid
            )
        if circ_policy.get('allow_requests'):
            item.request(
                patron_pid=requested_patron.pid,
                transaction_location_pid=user_location,
                transaction_user_pid=user_pid,
                transaction_date=transaction_date,
                pickup_location_pid=get_random_pickup_location(
                    requested_patron.pid),
                document_pid=item.replace_refs()['document']['pid'],
            )
    return item['barcode']


def create_request(barcode, transaction_type, loanable_items):
    """Create request transactions."""
    item = next(loanable_items)
    rank_1_patron = get_random_patron(barcode)
    patron = Patron.get_patron_by_barcode(barcode)
    if transaction_type == 'rank_2':
        transaction_date = (
            datetime.now(timezone.utc) - timedelta(2)).isoformat()
        user_pid, user_location = \
            get_random_librarian_and_transaction_location(patron)

        circ_policy = CircPolicy.provide_circ_policy(
                item.library_pid,
                rank_1_patron.patron_type_pid,
                item.item_type_pid
            )
        if circ_policy.get('allow_requests'):
            item.request(
                patron_pid=rank_1_patron.pid,
                transaction_location_pid=user_location,
                transaction_user_pid=user_pid,
                transaction_date=transaction_date,
                pickup_location_pid=get_random_pickup_location(
                    rank_1_patron.pid),
                document_pid=item.replace_refs()['document']['pid'],
            )
    transaction_date = datetime.now(timezone.utc).isoformat()
    user_pid, user_location = get_random_librarian_and_transaction_location(
        patron)
    item.request(
        patron_pid=patron.pid,
        transaction_location_pid=user_location,
        transaction_user_pid=user_pid,
        transaction_date=transaction_date,
        pickup_location_pid=get_random_pickup_location(patron.pid),
        document_pid=item.replace_refs()['document']['pid'],
    )
    return item['barcode']


def get_loanable_items(patron_type_pid):
    """Get the list of loanable items."""
    org_pid = PatronType.get_record_by_pid(patron_type_pid)\
                        .replace_refs()['organisation']['pid']
    loanable_items = ItemsSearch()\
        .filter('term', organisation__pid=org_pid)\
        .filter('term', status=ItemStatus.ON_SHELF).source(['pid']).scan()
    for loanable_item in loanable_items:
        item = Item.get_record_by_pid(loanable_item.pid)
        circ_policy = CircPolicy.provide_circ_policy(
                item.library_pid,
                patron_type_pid,
                item.item_type_pid
            )
        if (
            circ_policy.get('allow_checkout') and
            circ_policy.get('allow_requests')
        ):
            if not item.number_of_requests():
                yield item


def get_random_pickup_location(patron_pid):
    """Find a qualified pickup location."""
    pickup_locations_pids = list(Location.get_pickup_location_pids(patron_pid))
    return random.choice(pickup_locations_pids)


def get_loan_dates(transaction_type, item, patron):
    """Get loan dates."""
    duration = CircPolicy.provide_circ_policy(
        item.library_pid,
        patron.patron_type_pid,
        item.item_type_pid
    ).get('checkout_duration')

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


def get_random_patron(exclude_this_barcode):
    """Find a qualified patron other than exclude_this_barcode."""
    ptrn_to_exclude = Patron.get_patron_by_barcode(exclude_this_barcode)
    ptty_pid = ptrn_to_exclude.replace_refs()['patron_type']['pid']
    org_pid = PatronType.get_record_by_pid(
        ptty_pid).replace_refs()['organisation']['pid']
    patrons = PatronsSearch()\
        .filter('term', roles='patron')\
        .filter('term', organisation__pid=org_pid)\
        .source(['barcode']).scan()
    for patron in patrons:
        if patron.barcode != exclude_this_barcode:
            return Patron.get_patron_by_barcode(barcode=patron.barcode)


def get_random_librarian(patron):
    """Find a qualified staff user."""
    ptty_pid = patron.replace_refs()['patron_type']['pid']
    org_pid = PatronType.get_record_by_pid(
        ptty_pid).replace_refs()['organisation']['pid']
    patrons = PatronsSearch()\
        .filter('term', roles='librarian')\
        .filter('term', organisation__pid=org_pid)\
        .source(['pid']).scan()
    for patron in patrons:
        return Patron.get_record_by_pid(patron.pid)


def get_random_librarian_and_transaction_location(patron):
    """Find a qualified user data."""
    user = get_random_librarian(patron).replace_refs()
    library = Library.get_record_by_pid(user['library']['pid'])
    return user.pid, library.get_pickup_location_pid()
