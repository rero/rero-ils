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


from invenio_circulation.api import get_loan_for_item, \
    patron_has_active_loan_on_item
from invenio_circulation.proxies import current_circulation
from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..items_types.api import ItemType
from ..libraries_locations.api import LibraryWithLocations
from ..loans.api import Loan, LoanAction, es_flush, get_checkout_by_item_pid, \
    get_in_tranist_item_pid, get_loans_by_item_pid, \
    get_request_by_item_pid_by_patron_pid, get_requests_by_item_pid
from ..locations.api import Location
from ..transactions.api import CircTransaction
from .fetchers import item_id_fetcher
from .minters import item_id_minter
from .models import ItemStatus
from .providers import ItemProvider


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

    durations = {ItemType.get_pid_by_name('short'): 15}

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

    def cancel_item_loan(self, **kwargs):
        """Cancel a given item loan for a patron."""
        loan_pid = kwargs.get('loan_pid')
        prev_loan = Loan.get_record_by_pid(loan_pid)
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='cancel')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def loan_item(self, **kwargs):
        """Checkout item to the user."""
        if kwargs.get('loan_pid'):
            loan_pid = kwargs.get('loan_pid')
            prev_loan = Loan.get_record_by_pid(loan_pid)
        else:
            prev_loan = Loan.initiate()
            prev_loan['item_pid'] = self.pid
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='checkout')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def automatic_checkin(self, **kwargs):
        """Apply circ transactions for item."""
        return_rec = {'action_applied': {}}
        # transaction_location_pid = kwargs.get('transaction_location_pid')
        item_status = self.get('item_status')

        if item_status == ItemStatus.ON_LOAN:
            checkout_loan = get_checkout_by_item_pid(self.pid)
            params = dict(loan_pid=checkout_loan['loan_pid'])
            loan = self.return_item(**params)
            return_rec['action_applied'][LoanAction.CHECKIN] = loan.get(
                'loan_pid'
            )
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
            return_rec['action_applied'][LoanAction.RECEIVE] = loan.get(
                'loan_pid'
            )
        elif item_status == ItemStatus.MISSING:
            self.return_missing_item(**kwargs)
            return_rec['action_applied'] = LoanAction.RETURN_MISSING
        else:
            return_rec = self
        return return_rec

    def receive_item(self, **kwargs):
        """Receive an item."""
        loan_pid = kwargs.get('loan_pid')
        prev_loan = Loan.get_record_by_pid(loan_pid)
        if not kwargs.get('item_pid'):
            kwargs['item_pid'] = self.pid
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='receive')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def return_item(self, **kwargs):
        """Checkin a given item."""
        loan_pid = kwargs.get('loan_pid')
        prev_loan = Loan.get_record_by_pid(loan_pid)
        if not kwargs.get('item_pid'):
            kwargs['item_pid'] = self.pid
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='checkin')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def request_item(self, **kwargs):
        """Request item for the user."""
        if kwargs.get('loan_pid'):
            loan_pid = kwargs.get('loan_pid')
            prev_loan = Loan.get_record_by_pid(loan_pid)
        else:
            prev_loan = Loan.initiate()
            prev_loan['item_pid'] = self.pid
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='request')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def extend_loan(self, **kwargs):
        """Renew a given item."""
        loan_pid = kwargs.get('loan_pid')
        prev_loan = Loan.get_record_by_pid(loan_pid)
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='extend')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

    def validate_item_request(self, **kwargs):
        """Validate item request."""
        loan_pid = kwargs.get('loan_pid')
        prev_loan = Loan.get_record_by_pid(loan_pid)
        params = dict(prev_loan, **kwargs)
        loan = current_circulation.circulation.trigger(
            prev_loan, **dict(params, trigger='validate')
        )
        es_flush()
        self.item_status_update()
        CircTransaction.create(loan)
        return loan

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
    def duration(self):
        """Get loan/extend duration based on item type."""
        return self.durations.get(self['item_type_pid'], self.default_duration)

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
            document_pid = DocumentsWithItems.document_retriever(self.pid)
            data['document_pid'] = document_pid
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
