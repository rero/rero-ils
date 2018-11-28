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

"""API for manipulating items."""

from datetime import datetime, timezone
from functools import wraps

from invenio_circulation.api import get_loan_for_item, \
    patron_has_active_loan_on_item
from invenio_circulation.errors import TransitionConditionsFailed
from invenio_circulation.proxies import current_circulation
from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..items_types.api import ItemType
from ..libraries_locations.api import LibraryWithLocations
from ..loans.api import Loan, LoanAction, es_flush, get_checkout_by_item_pid, \
    get_in_tranist_item_pid, get_loan_by_item_pid_by_patron_pid, \
    get_loans_by_item_pid, get_request_by_item_pid_by_patron_pid, \
    get_requests_by_item_pid
from ..locations.api import Location
from ..transactions.api import CircTransaction
from .fetchers import item_id_fetcher
from .minters import item_id_minter
from .models import ItemStatus
from .providers import ItemProvider


def add_missing_action_params(function):
    """Add missing action parameters."""
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        kwargs['item_pid'] = item.pid
        kwargs['document_pid'] = item.dumps().get('document_pid')

        action_required_params = item.action_required_params.copy()
        from ..patrons.api import current_patron
        loan = None
        loan_pid = kwargs.get('loan_pid')

        if loan_pid:
            loan = Loan.get_record_by_pid(loan_pid)
        else:
            patron_pid = kwargs.get('patron_pid')
            if patron_pid:
                prev_loan = get_loan_by_item_pid_by_patron_pid(
                    item.pid, patron_pid)
                if prev_loan:
                    loan = prev_loan
                else:
                    if function.__name__ in ('loan_item', 'request_item'):
                        loan = Loan.initiate()
                        loan['item_pid'] = item.pid
                        loan['patron_pid'] = patron_pid

        if loan:
            kwargs['current_loan'] = loan
            kwargs['patron_pid'] = loan.get('patron_pid')
            kwargs['loan_pid'] = loan.get('loan_pid')
        missing = [
            p
            for p in action_required_params
            if p not in kwargs
        ]
        if missing:
            if 'patron_pid' in missing:
                raise TransitionConditionsFailed('patron pid not found')
            if 'transaction_date' in missing:
                kwargs['transaction_date'] = datetime.now(
                    timezone.utc).isoformat()
            if 'transaction_user_pid' in missing:
                user = current_patron
                kwargs['transaction_user_pid'] = user.pid
            if 'transaction_location_pid' in missing:
                user = current_patron.dumps()
                kwargs['transaction_location_pid'] = user.get(
                    'circulation_location_pid')
        return function(item, *args, **kwargs)
    return wrapper


class ItemsSearch(RecordsSearch):
    """ItemsSearch."""

    class Meta:
        """Search only on item index."""

        index = 'items'


class Item(IlsRecord):
    """Item class."""

    minter = item_id_minter
    fetcher = item_id_fetcher
    provider = ItemProvider

    default_duration = 30

    action_required_params = [
        'patron_pid',
        'transaction_location_pid',
        'transaction_user_pid',
        'transaction_date',
        'item_pid',
        'document_pid',
    ]

    def __post_loan_process(self, loan):
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)

    @property
    def status(self):
        """Shortcut for item status."""
        return self.get('item_status', '')

    @classmethod
    def create(cls, data, id_=None, delete_pid=True, **kwargs):
        """Create a new item record."""
        return super(Item, cls).create(
            data, id_=id_, delete_pid=delete_pid, **kwargs
        )

    def item_status_update(self):
        """Update item status."""
        statuses = {
            'ITEM_ON_LOAN': 'on_loan',
            'ITEM_AT_DESK': 'at_desk',
            'ITEM_IN_TRANSIT_FOR_PICKUP': 'in_transit',
            'ITEM_IN_TRANSIT_TO_HOUSE': 'in_transit',
        }
        loan = get_loan_for_item(self.pid)
        if loan:
            self['item_status'] = statuses[loan.get('state')]
        else:
            if self['item_status'] != ItemStatus.MISSING:
                self['item_status'] = ItemStatus.ON_SHELF

        self.commit()
        self.dbcommit(reindex=True, forceindex=True)

        from ..documents_items.api import DocumentsWithItems

        document = DocumentsWithItems.get_document_by_itemid(self.id)
        document.reindex()

    @classmethod
    def get_item_by_barcode(cls, barcode=None):
        """Get item by barcode."""
        search = ItemsSearch()
        result = (
            search.filter('term', barcode=barcode)
            .source(includes='pid')
            .execute()
            .to_dict()
        )
        try:
            result = result['hits']['hits'][0]
            return super(IlsRecord, cls).get_record(result['_id'])
        except Exception:
            return None

    @add_missing_action_params
    def cancel_item_loan(self, **kwargs):
        """Cancel a given item loan for a patron."""
        current_loan = kwargs.pop('current_loan', None)
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='cancel')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def automatic_checkin(self, **kwargs):
        """Apply circ transactions for item."""
        return_rec = self.dumps()
        return_rec['action_applied'] = {}
        # transaction_location_pid = kwargs.get('transaction_location_pid')
        item_status = self.get('item_status')

        if item_status == ItemStatus.ON_LOAN:
            checkout_loan = get_checkout_by_item_pid(self.pid)
            params = dict(loan_pid=checkout_loan['loan_pid'])
            loan = self.return_item(**params)
            return_rec['action_applied'][LoanAction.CHECKIN] = loan.dumps()

            # TODO: automatic validation
            # requests = self.dumps().get('pending_loans')
            # if len(requests):
            #     next_loan = Loan.get_record_by_pid(requests[0])
            #     pickup_location_pid = next_loan.get('pickup_location_pid')
            #     if transaction_location_pid == pickup_location_pid:
            #         params = dict(next_loan, **kwargs)
            #         next_loan = current_circulation.circulation.trigger(
            #             next_loan, **dict(params, trigger='validate')
            #         )
            #         return_rec['action_applied'][
            #             LoanAction.VALIDATE] = next_loan.get(
            #             'loan_pid'
            #         )

        elif item_status == ItemStatus.IN_TRANSIT:
            in_transit_loan = get_in_tranist_item_pid(self.pid)
            params = dict(loan_pid=in_transit_loan['loan_pid'])
            loan = self.receive_item(**params)
            return_rec['action_applied'][LoanAction.RECEIVE] = loan.dumps()

        elif item_status == ItemStatus.MISSING:
            self.return_missing_item(**kwargs)
            return_rec['action_applied'][
                LoanAction.RETURN_MISSING] = {}

        return return_rec

    def lose_item(self):
        """Lose the given item.

        This sets the status to ItemStatus.MISSING.
        All existing holdings will be canceled.
        """
        for loan in get_loans_by_item_pid(self.pid):
            loan_pid = loan['loan_pid']
            self.cancel_item_loan(loan_pid=loan_pid)

        self['item_status'] = ItemStatus.MISSING
        self.item_status_update()

    def return_missing_item(self, **kwargs):
        """Return the missing item.

        The item's status will be set to ItemStatus.ON_SHELF.
        """
        self['item_status'] = ItemStatus.ON_SHELF
        self.item_status_update()
        self.commit()
        self.dbcommit(reindex=True, forceindex=True)

    @property
    def requests(self):
        """Get the list of requests."""
        request_list = []
        requests = get_requests_by_item_pid(self.pid)
        if requests:
            for request in requests:
                request_list.append(request)
        return request_list

    @property
    def available(self):
        """Get availability for loan."""
        return (
            self.status == ItemStatus.ON_SHELF and
            self.number_of_item_requests() == 0
        )

    @property
    def can_delete(self):
        """Record can be deleted."""
        return self.available

    def get_item_end_date(self):
        """Get item due date a given item."""
        loan = get_loan_for_item(self.pid)
        if loan:
            end_date = loan['end_date']
            # due_date = datetime.strptime(end_date, '%Y-%m-%d')
            from ...filter import format_date_filter
            from invenio_i18n.ext import current_i18n

            due_date = format_date_filter(
                end_date,
                format='short_date',
                locale=current_i18n.locale.language,
            )
            return due_date
        return None

    def get_renewal_count(self):
        """Get item renewal count."""
        loan = get_loan_for_item(self.pid)
        if loan:
            renewal_count = loan['extension_count']
            if renewal_count:
                return renewal_count
        return 0

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(IlsRecord, self).dumps(**kwargs)
        location_pid = data.get('location_pid')
        location = Location.get_record_by_pid(location_pid)
        from ..documents_items.api import DocumentsWithItems

        if DocumentsWithItems.document_retriever(self.pid):
            document = DocumentsWithItems.get_document_by_itemid(self.id)
            data['document_pid'] = document.pid
            data['document_title'] = document.get('title')
            data['document_authors'] = document.get('authors')
        if location:
            data['location_name'] = location.get('name')
            library = LibraryWithLocations.get_library_by_locationid(
                location.id
            )
            data['library_pid'] = library.pid
            data['library_name'] = library.get('name')
        data['requests_count'] = self.number_of_item_requests()
        data['available'] = self.available
        item_type_name = ItemType.get_record_by_pid(data.get('item_type_pid'))[
            'name'
        ]
        data['item_type_name'] = item_type_name
        requests = get_requests_by_item_pid(self.pid)
        pending_loans = []
        if requests:
            for request in requests:
                pending_loans.append(request.get('loan_pid'))
        data['pending_loans'] = pending_loans
        return data

    def number_of_item_requests(self):
        """Get number of requests for a given item."""
        number_requests = 0
        for loan in get_requests_by_item_pid(self.pid):
            number_requests += 1

        return number_requests

    def patron_request_rank(self, patron_barcode):
        """Get the rank of patron in list of requests on this item."""
        from ..patrons.api import Patron

        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            rank = 0
            requests = get_requests_by_item_pid(self.pid)
            if requests:
                for request in requests:
                    rank += 1
                    if request['patron_pid'] == patron.pid:
                        return rank
        return False

    def requested_by_patron(self, patron_barcode):
        """Check if the item is requested by a given patron."""
        from ..patrons.api import Patron

        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            request = get_request_by_item_pid_by_patron_pid(
                item_pid=self.pid, patron_pid=patron.pid
            )
            if request:
                return True
        return False

    def loaned_to_patron(self, patron_barcode):
        """Check if the item is loaned by a given patron."""
        from ..patrons.api import Patron

        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            patron_pid = patron.pid
            checkout = patron_has_active_loan_on_item(patron_pid, self.pid)
            if checkout:
                return True
        return False

    @classmethod
    def item_location_retriever(cls, item_pid, **kwargs):
        """Get item location."""
        location_pid = ''
        if cls.get_record_by_pid(item_pid):
            item = cls.get_record_by_pid(item_pid)
            if item.get('location_pid'):
                location_pid = item.get('location_pid')
        return location_pid

    @add_missing_action_params
    def validate_item_request(self, **kwargs):
        """Validate item request."""
        current_loan = kwargs.pop('current_loan', None)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='validate')
        )
        self.__post_loan_process(loan)
        return loan

    @add_missing_action_params
    def extend_loan(self, **kwargs):
        """Extend checkout duration for this item."""
        current_loan = kwargs.pop('current_loan', None)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='extend')
        )
        self.__post_loan_process(loan)
        return loan

    @add_missing_action_params
    def request_item(self, **kwargs):
        """Request item for the user."""
        current_loan = kwargs.pop('current_loan', None)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='request')
        )
        self.__post_loan_process(loan)
        return loan

    @add_missing_action_params
    def receive_item(self, **kwargs):
        """Receive an item."""
        current_loan = kwargs.pop('current_loan', None)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='receive')
        )
        self.__post_loan_process(loan)
        return loan

    @add_missing_action_params
    def return_item(self, **kwargs):
        """Checkin a given item."""
        current_loan = kwargs.pop('current_loan', None)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkin')
        )
        self.__post_loan_process(loan)
        return loan

    @add_missing_action_params
    def loan_item(self, **kwargs):
        """Checkout item to the user."""
        current_loan = kwargs.pop('current_loan', None)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkout')
        )
        self.__post_loan_process(loan)
        return loan
