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
import traceback
from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext
from invenio_circulation.api import get_loan_for_item

from ..circ_policies.api import CircPolicy
from ..items.api import Item, ItemsSearch, ItemStatus
from ..libraries.api import Library
from ..loans.api import Loan
from ..locations.api import Location
from ..notifications.tasks import create_over_and_due_soon_notifications
from ..patron_types.api import PatronType
from ..patrons.api import Patron, PatronsSearch


@click.command('create_loans')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def create_loans(infile, verbose, debug):
    """Create circulation transactions.

    infile: Json transactions file
    """
    click.secho('Create circulation transactions:', fg='green')
    data = json.load(infile)
    errors_count = {}
    for patron_data in data:
        barcode = patron_data.get('barcode')
        if barcode is None:
            click.secho('Patron barcode is missing!', fg='red')
        else:
            click.echo('Patron: {barcode}'.format(barcode=barcode))
            loans = patron_data.get('loans', {})
            requests = patron_data.get('requests', {})
            patron_type_pid = Patron.get_patron_by_barcode(
                barcode).patron_type_pid
            loanable_items = get_loanable_items(patron_type_pid)
            if verbose:
                loanable_items_count = len(
                    list(get_loanable_items(patron_type_pid))
                )
                msg = '\t{patron} loanable_items: {loanable_items}'.format(
                    patron=patron_data,
                    loanable_items=loanable_items_count
                )
                click.echo(msg)

            for transaction in range(loans.get('active', 0)):
                item_barcode = create_loan(barcode, 'active', loanable_items,
                                           verbose, debug)
                errors_count = print_message(item_barcode, 'active',
                                             errors_count)

            for transaction in range(loans.get('overdue', 0)):
                item_barcode = create_loan(barcode, 'overdue', loanable_items,
                                           verbose, debug)
                errors_count = print_message(item_barcode, 'overdue',
                                             errors_count)

            for transaction in range(loans.get('extended', 0)):
                item_barcode = create_loan(barcode, 'extended', loanable_items,
                                           verbose, debug)
                errors_count = print_message(item_barcode, 'extended',
                                             errors_count)

            for transaction in range(loans.get('requested_by_others', 0)):
                item_barcode = create_loan(barcode, 'requested_by_others',
                                           loanable_items, verbose, debug)
                errors_count = print_message(item_barcode,
                                             'requested_by_others',
                                             errors_count)

            for transaction in range(requests.get('requests', 0)):
                item_barcode = create_request(barcode, 'requests',
                                              loanable_items, verbose, debug)
                errors_count = print_message(item_barcode, 'requests',
                                             errors_count)

            for transaction in range(requests.get('rank_1', 0)):
                item_barcode = create_request(barcode, 'rank_1',
                                              loanable_items, verbose, debug)
                errors_count = print_message(item_barcode, 'rank_1',
                                             errors_count)

            for transaction in range(requests.get('rank_2', 0)):
                item_barcode = create_request(barcode, 'rank_2',
                                              loanable_items, verbose, debug)
                errors_count = print_message(item_barcode, 'rank_2',
                                             errors_count)
    # create due soon notifications, overdue notifications are auto created.
    create_over_and_due_soon_notifications(overdue=False)
    for key, val in errors_count.items():
        click.secho(
            'Errors {transaction_type}: {count}'.format(
                transaction_type=key,
                count=val
            ),
            fg='red'
        )


def print_message(item_barcode, transaction_type, errors_count):
    """Print confirmation message."""
    if item_barcode:
        click.echo('\titem {item_barcode}: {transaction_type}'.format(
            transaction_type=transaction_type,
            item_barcode=item_barcode
        ))
    else:
        click.secho(
            '\tcreation error: {transaction_type}'.format(
                transaction_type=transaction_type,
            ),
            fg='red'
        )
        errors_count.setdefault(transaction_type, 0)
        errors_count[transaction_type] += 1
    return errors_count


def create_loan(barcode, transaction_type, loanable_items, verbose=False,
                debug=False):
    """Create loans transactions."""
    try:
        item = next(loanable_items)
        patron = Patron.get_patron_by_barcode(barcode=barcode)
        transaction_date = datetime.now(timezone.utc).isoformat()
        user_pid, user_location = \
            get_random_librarian_and_transaction_location(patron)
        item.checkout(
            patron_pid=patron.pid,
            transaction_user_pid=user_pid,
            transaction_location_pid=user_location,
            transaction_date=transaction_date,
            document_pid=item.replace_refs()['document']['pid'],
            item_pid=item.pid,
        )
        loan = get_loan_for_item(item.pid)
        loan_pid = loan.get('pid')
        loan = Loan.get_record_by_pid(loan_pid)
        if transaction_type == 'overdue':
            end_date = datetime.now(timezone.utc) - timedelta(days=2)
            loan['end_date'] = end_date.isoformat()
            loan.update(
                loan,
                dbcommit=True,
                reindex=True
            )
            loan.create_notification(notification_type='due_soon')

            end_date = datetime.now(timezone.utc) - timedelta(days=70)
            loan['end_date'] = end_date.isoformat()
            loan.update(
                loan,
                dbcommit=True,
                reindex=True
            )
            loan.create_notification(notification_type='overdue')

        elif transaction_type == 'extended':
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
        elif transaction_type == 'requested_by_others':
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
                loan.create_notification(notification_type='recall')
        return item['barcode']
    except Exception as err:
        if verbose:
            click.secho(
                '\tException loan {transaction_type}: {err}'.format(
                    transaction_type=transaction_type,
                    err=err
                ),
                fg='red'
            )
        if debug:
            traceback.print_exc()
        return None


def create_request(barcode, transaction_type, loanable_items, verbose=False,
                   debug=False):
    """Create request transactions."""
    try:
        item = next(loanable_items)
        rank_1_patron = get_random_patron(barcode)
        patron = Patron.get_patron_by_barcode(barcode)
        if transaction_type == 'rank_2':
            transaction_date = \
                (datetime.now(timezone.utc) - timedelta(2)).isoformat()
            user_pid, user_location = \
                get_random_librarian_and_transaction_location(patron)

            circ_policy = CircPolicy.provide_circ_policy(
                item.holding_library_pid,
                rank_1_patron.patron_type_pid,
                item.holding_circulation_category_pid
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
        user_pid, user_location = \
            get_random_librarian_and_transaction_location(patron)
        item.request(
            patron_pid=patron.pid,
            transaction_location_pid=user_location,
            transaction_user_pid=user_pid,
            transaction_date=transaction_date,
            pickup_location_pid=get_random_pickup_location(patron.pid),
            document_pid=item.replace_refs()['document']['pid'],
        )
        return item['barcode']
    except Exception as err:
        if verbose:
            click.secho(
                '\tException request {transaction_type}: {err}'.format(
                    transaction_type=transaction_type,
                    err=err
                ),
                fg='red'
            )
        if debug:
            traceback.print_exc()
        return None


def get_loanable_items(patron_type_pid):
    """Get the list of loanable items."""
    org_pid = PatronType.get_record_by_pid(patron_type_pid)\
                        .replace_refs()['organisation']['pid']
    loanable_items = ItemsSearch()\
        .filter('term', organisation__pid=org_pid)\
        .filter('term', status=ItemStatus.ON_SHELF).source(['pid']).scan()
    for loanable_item in loanable_items:
        item = Item.get_record_by_pid(loanable_item.pid)
        if item:
            circ_policy = CircPolicy.provide_circ_policy(
                item.holding_library_pid,
                patron_type_pid,
                item.holding_circulation_category_pid
            )
            if (
                    circ_policy.get('allow_checkout') and
                    circ_policy.get('allow_requests')
            ):
                if not item.number_of_requests():
                    # exclude the first 16 items of the 3rd organisation
                    barcode = item.get('barcode')
                    if not (
                        barcode.startswith('fictive') and
                        int(barcode.split('fictive')[1]) < 17
                    ):
                        yield item


def get_random_pickup_location(patron_pid):
    """Find a qualified pickup location."""
    pickup_locations_pids = list(Location.get_pickup_location_pids(patron_pid))
    return random.choice(pickup_locations_pids)


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
    return None


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
    return None


def get_random_librarian_and_transaction_location(patron):
    """Find a qualified user data."""
    user = get_random_librarian(patron).replace_refs()
    library = Library.get_record_by_pid(user['library']['pid'])
    return user.pid, library.get_pickup_location_pid()
