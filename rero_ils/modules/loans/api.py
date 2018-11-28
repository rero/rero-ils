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

"""API for manipulating Loans."""


import uuid

from flask import current_app, url_for
from invenio_circulation.api import Loan as BaseLoan
from invenio_circulation.errors import CirculationException
from invenio_circulation.pidstore.fetchers import loan_pid_fetcher
from invenio_circulation.pidstore.minters import loan_pid_minter
from invenio_circulation.pidstore.providers import CirculationLoanIdProvider
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item, \
    search_by_patron_pid, search_by_pid
from invenio_db import db
from invenio_indexer.api import RecordIndexer


class LoanAction(object):
    """Class holding all availabe circulation loan actions."""

    REQUEST = 'request'
    CHECKOUT = 'checkout'
    CHECKIN = 'checkin'
    VALIDATE = 'validate'
    RECEIVE = 'receive'
    RETURN_MISSING = 'return_missing'


class Loan(BaseLoan):
    """Loan class."""

    minter = loan_pid_minter
    fetcher = loan_pid_fetcher
    provider = CirculationLoanIdProvider

    @property
    def pid(self):
        """Shortcut for loan pid."""
        return self.get('loan_pid', '')

    @classmethod
    def initiate(cls):
        """Create a new loan with CREATED state."""
        record_uuid = uuid.uuid4()
        new_loan = {}
        loan_pid_minter(record_uuid, data=new_loan)
        loan = cls.create(data=new_loan, id_=record_uuid)
        db.session.commit()
        RecordIndexer().index(loan)
        return loan

    def build_url_action_for_pid(self, action):
        """Build urls for Loan actions."""
        mapping = {
            'checkout': 'loan_item',
            'validate': 'validate_item_request',
            'receive': 'receive_item',
            'checkin': 'return_item',
            'request': 'request_item',
            'extend': 'extend_loan',
            'cancel': 'cancel',
        }
        item_pid_value = self.get('item_pid', '')
        location = self.get('pickup_location_pid', '')
        if action != 'request':
            url = url_for('items.' + mapping[action])
        else:
            if self['state'] == 'CREATED':
                # TODO: find a cleaner way to do this.
                # request is the only action that requires two parameters
                action = 'cancel'
                url = url_for('items.' + mapping[action]).replace(
                    'cancel', 'request'
                )
            else:
                url = url_for(
                    'items.' + mapping[action],
                    item_pid_value=item_pid_value,
                    location=location,
                )
        return url

    def loan_links_factory(self):
        """Factory for links generation."""
        links = {}
        actions = {}
        transitions_config = current_app.config.get(
            'CIRCULATION_LOAN_TRANSITIONS', {}
        )
        for transition in transitions_config.get(self['state']):
            action = transition.get('trigger', 'next')
            actions[action] = self.build_url_action_for_pid(action)
        links.setdefault('actions', actions)
        return links

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(Loan, self).dumps(**kwargs)
        data['links'] = self.loan_links_factory()
        if self.get('item_pid'):
            from ..items.api import Item

            item = Item.get_record_by_pid(self['item_pid']).dumps()
            data['item_location_pid'] = item['location_pid']
            data['item_location_name'] = item['location_name']
            data['item_library_name'] = item['library_name']
            data['item_library_pid'] = item['library_pid']
            data['item_barcode'] = item['barcode']
            data['item_call_number'] = item.get('call_number', '')
        from ..locations.api import Location

        if self.get('transaction_location_pid'):
            location_pid = self.get('transaction_location_pid')
            transaction_location_name = Location.get_record_by_pid(
                location_pid
            ).get('name')
            data['transaction_location_name'] = transaction_location_name
            from ..libraries_locations.api import LibraryWithLocations

            location = Location.get_record_by_pid(location_pid)
            library = LibraryWithLocations.get_library_by_locationid(
                location.id
            )
            data['transaction_library_pid'] = library.get('pid')
            data['transaction_library_name'] = library.get('name')
        if self.get('pickup_location_pid'):
            location_pid = self.get('pickup_location_pid')
            pickup_location_name = Location.get_record_by_pid(
                location_pid).get(
                'name'
            )
            data['pickup_location_name'] = pickup_location_name
        if self.get('transaction_user_pid'):
            user_pid = self.get('transaction_user_pid')
            from ..patrons.api import Patron
            from ..libraries.api import Library

            user = Patron.get_record_by_pid(user_pid)
            if user.get('library_pid'):
                library_pid = user.get('library_pid')
                data['user_library_pid'] = library_pid
                data['user_library_name'] = Library.get_record_by_pid(
                    library_pid
                ).get('name')
            else:
                data['user_library_pid'] = data['transaction_library_pid']
                data['user_library_name'] = data['transaction_library_name']
        if self.get('document_pid'):
            from ..documents_items.api import DocumentsWithItems

            document_pid = self.get('document_pid')
            document = DocumentsWithItems.get_record_by_pid(document_pid)
            data['document_title'] = document.get('title')
            data['document_authors'] = document.get('authors')
        if self.get('patron_pid'):
            patron_pid = self.get('patron_pid')
            from ..patrons.api import Patron

            patron = Patron.get_record_by_pid(patron_pid).dumps()
            data['patron_name'] = patron.get('name')
            data['patron_barcode'] = patron.get('barcode')
        return data

    def cancel_loan(self, **kwargs):
        """Cancel a given loan for a patron."""
        loan_pid = kwargs.get('loan_pid')
        prev_loan = Loan.get_record_by_pid(loan_pid)
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='cancel')
        )
        es_flush()
        return loan


def get_pending_loan_by_patron_and_item(patron_pid, item_pid):
    """Return loan if patron has a pending or active Loan for given item."""
    if not patron_pid or not item_pid:
        raise CirculationException('Patron PID or Item PID not specified')

    search = search_by_patron_item(
        patron_pid=patron_pid, item_pid=item_pid, filter_states=['PENDING']
    )
    search_result = search.execute()
    if search_result.hits:
        return search_result.hits.hits[0]['_source']
    else:
        return {}


def get_checkout_by_item_pid(item_pid):
    """Return any ITEM_ON_LOAN loan for item."""
    search = search_by_pid(item_pid=item_pid, filter_states=['ITEM_ON_LOAN'])
    search_result = search.execute()
    if search_result.hits:
        return search_result.hits.hits[0]['_source']
    return {}


def get_in_tranist_item_pid(item_pid):
    """Return any IN_TRANSIT_FOR_PICKUP loan for item."""
    search = search_by_pid(
        item_pid=item_pid,
        filter_states=[
            'ITEM_IN_TRANSIT_FOR_PICKUP',
            'ITEM_IN_TRANSIT_TO_HOUSE',
        ],
    )
    search_result = search.execute()
    if search_result.hits:
        return search_result.hits.hits[0]['_source']
    return {}


def get_loans_by_item_pid(item_pid):
    """Return any loan loans for item."""
    search = search_by_pid(item_pid=item_pid)
    for result in search.scan():
        yield Loan.get_record_by_pid(result[Loan.pid_field])


def get_request_by_item_pid_by_patron_pid(item_pid, patron_pid):
    """Get pending, item_on_transit, item_at_desk loans for item, patron."""
    search = search_by_patron_item(
        item_pid=item_pid,
        patron_pid=patron_pid,
        filter_states=[
            'PENDING',
            'ITEM_AT_DESK',
            'ITEM_IN_TRANSIT_FOR_PICKUP',
            'ITEM_IN_TRANSIT_TO_HOUSE',
        ],
    )
    search_result = search.execute()
    if search_result.hits:
        return search_result.hits.hits[0]['_source']
    return {}


def get_loans_by_patron_pid(patron_pid):
    """Return all checkout for patron."""
    if not patron_pid:
        raise CirculationException('Patron PID not specified')

    search = search_by_patron_pid(patron_pid=patron_pid)
    for result in search.sort('transaction_date', {'order': 'asc'}).scan():
        yield Loan.get_record_by_pid(result[Loan.pid_field])


def es_flush():
    """Flush index."""
    from invenio_indexer.api import RecordIndexer

    RecordIndexer().client.indices.flush()


def get_requests_by_item_pid(item_pid):
    """Return any pending or item_on_transit or item_at_desk loans for item."""
    search = current_circulation.loan_search
    search = search.params(preserve_order=True).filter(
        'term',
        item_pid=item_pid
    )
    search = search.filter(
        'terms',
        state=['PENDING', 'ITEM_AT_DESK', 'ITEM_IN_TRANSIT_FOR_PICKUP'])
    search = search.sort({'transaction_date': {'order': 'asc'}})
    for result in search.scan():
        yield Loan.get_record_by_pid(result[Loan.pid_field])


def get_pendings_by_library_pid(library_pid):
    """Retrieve loans attached to a given library."""
    search = current_circulation.loan_search
    search = search.params(preserve_order=True).filter(
        'term',
        item_library_pid=library_pid
    )
    search = search.filter('term', state='PENDING')
    search = search.sort({'transaction_date': {'order': 'asc'}})
    for result in search.scan():
        yield result


def item_has_active_loans(item_pid):
    """Check if item has active loans."""
    search = search_by_pid(
        item_pid=item_pid,
        filter_states=current_app.config['CIRCULATION_STATES_LOAN_ACTIVE'],
    ).source([])
    hits = search.execute()
    if len(hits):
        return True
    return False


def get_loan_by_item_pid_by_patron_pid(item_pid, patron_pid):
    """Get loan for item, patron."""
    search_result = search_by_patron_item(
        patron_pid=patron_pid,
        item_pid=item_pid,
        filter_states=[
            'PENDING',
            'ITEM_AT_DESK',
            'ITEM_IN_TRANSIT_FOR_PICKUP',
            'ITEM_IN_TRANSIT_TO_HOUSE',
            'ITEM_ON_LOAN',
        ],
    ).execute()
    results = search_result.hits.total
    if results == 1:
        loan_pid = search_result.hits.hits[0]['_source']['loan_pid']
        return Loan.get_record_by_pid(loan_pid)
    else:
        return {}
