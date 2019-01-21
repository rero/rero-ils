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
from functools import partial, wraps

from invenio_circulation.api import get_loan_for_item, \
    patron_has_active_loan_on_item
from invenio_circulation.errors import CirculationException, \
    NoValidTransitionAvailable
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_pid
from invenio_search import current_search

from ..api import IlsRecord, IlsRecordIndexer, IlsRecordsSearch
from ..documents.api import Document
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..loans.api import Loan, LoanAction, get_request_by_item_pid_by_patron_pid
from ..minters import id_minter
from ..patrons.api import Patron, current_patron
from ..transactions.api import CircTransaction
from .models import ItemStatus
from .providers import ItemProvider

# minter
item_id_minter = partial(id_minter, provider=ItemProvider)

# fetcher
item_id_fetcher = partial(id_fetcher, provider=ItemProvider)


class ItemsIndexer(IlsRecordIndexer):
    """."""

    def index(self, record):
        """."""
        return_value = super(ItemsIndexer, self).index(record)
        document_pid = record.replace_refs()['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        return return_value


class ItemsSearch(IlsRecordsSearch):
    """ItemsSearch."""

    class Meta:
        """Search only on item index."""

        index = 'items'


def add_loans_parameters_and_flush_indexes(function):
    """Add missing action parameters."""
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        """."""
        loan = None
        web_request = False
        patron_pid = kwargs.get('patron_pid')
        loan_pid = kwargs.get('loan_pid')
        # TODO: include in invenio-circulation
        if function.__name__ == 'request' and \
                not kwargs.get('pickup_location_pid'):
            raise CirculationException(
                "Pickup Location PID not specified")

        if loan_pid:
            loan = Loan.get_record_by_pid(loan_pid)
        elif function.__name__ in ('checkout', 'request'):
            if function.__name__ == 'request' and not patron_pid:
                patron_pid = current_patron.pid
                web_request = True
            # create or get a loan
            if not patron_pid:
                raise CirculationException(
                    "Patron PID not specified")
            data = {
                'item_pid': item.pid,
                'patron_pid': patron_pid
            }
            loan = Loan.create(data, dbcommit=True, reindex=True)
        else:
            raise CirculationException(
                "Loan PID not specified")

        # set missing parameters
        kwargs['item_pid'] = item.pid
        kwargs['patron_pid'] = loan.get('patron_pid')
        kwargs['loan_pid'] = loan.get('loan_pid')
        kwargs.setdefault(
            'transaction_date', datetime.now(timezone.utc).isoformat())
        if not kwargs.get('transaction_user_pid'):
            kwargs.setdefault(
                'transaction_user_pid', current_patron.pid)
        kwargs.setdefault(
            'document_pid', item.replace_refs().get('document', {}).get('pid'))
        # TODO: change when it will be fixed in circulation
        if web_request:
            kwargs.setdefault(
                'transaction_location_pid', kwargs.get('pickup_location_pid'))
        elif not kwargs.get('transaction_location_pid'):
            kwargs.setdefault(
                'transaction_location_pid', Library.get_record_by_pid(
                    current_patron.replace_refs()['library']['pid']
                ).get_pickup_location_pid())

        item, action_applied = function(item, loan, *args, **kwargs)

        # commit and reindex item and loans
        current_search.flush_and_refresh(
            current_circulation.loan_search.Meta.index)
        item.status_update(dbcommit=True, reindex=True, forceindex=True)
        ItemsSearch.flush()
        CircTransaction.create(loan)
        return item, action_applied
    return wrapper


class Item(IlsRecord):
    """Item class."""

    minter = item_id_minter
    fetcher = item_id_fetcher
    provider = ItemProvider

    default_duration = 30

    @classmethod
    def get_document_pid_by_item_pid(cls, item_pid):
        """."""
        item = cls.get_record_by_pid(item_pid).replace_refs()
        return item.get('document', {}).get('pid')

    @classmethod
    def get_items_pid_by_document_pid(cls, document_pid):
        """."""
        results = ItemsSearch()\
            .filter('term', document__pid=document_pid)\
            .source(['pid']).scan()
        for r in results:
            yield r.pid

    @classmethod
    def get_loans_by_item_pid(cls, item_pid):
        """Return any loan loans for item."""
        results = current_circulation.loan_search.filter(
            'term', item_pid=item_pid).source(includes='loan_pid').scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.loan_pid)

    @classmethod
    def get_loan_pid_with_item_on_loan(cls, item_pid):
        """."""
        search = search_by_pid(
            item_pid=item_pid, filter_states=['ITEM_ON_LOAN'])
        results = search.source(['loan_pid']).scan()
        try:
            return next(results).loan_pid
        except StopIteration:
            return None

    @classmethod
    def get_loan_pid_with_item_in_transit(cls, item_pid):
        """."""
        search = search_by_pid(
            item_pid=item_pid, filter_states=[
                "ITEM_IN_TRANSIT_FOR_PICKUP",
                "ITEM_IN_TRANSIT_TO_HOUSE"])
        results = search.source(['loan_pid']).scan()
        try:
            return next(results).loan_pid
        except StopIteration:
            return None

    @classmethod
    def get_item_by_barcode(cls, barcode=None):
        """Get item by barcode."""
        results = ItemsSearch().filter(
            'term', barcode=barcode).source(includes='pid').scan()
        try:
            return cls.get_record_by_pid(next(results).pid)
        except StopIteration:
            return None

    @classmethod
    def get_pendings_loans(cls, library_pid):
        """."""
        # check library exists
        lib = Library.get_record_by_pid(library_pid)
        if not lib:
            raise Exception(msg='Invalid Library PID')

        results = current_circulation.loan_search\
            .source(['loan_pid'])\
            .params(preserve_order=True)\
            .filter('term', state='PENDING')\
            .filter('term', library_pid=library_pid)\
            .sort({'transaction_date': {'order': 'asc'}})\
            .scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.loan_pid)

    def get_requests(self):
        """Return any pending, item_on_transit, item_at_desk loans."""
        search = search_by_pid(
            item_pid=self.pid, filter_states=[
                'PENDING',
                'ITEM_AT_DESK',
                'ITEM_IN_TRANSIT_FOR_PICKUP'
            ]).params(preserve_order=True)\
            .source(['loan_pid'])\
            .sort({'transaction_date': {'order': 'asc'}})
        for result in search.scan():
            yield Loan.get_record_by_pid(result.loan_pid)

    @classmethod
    def get_requests_to_validate(cls, library_pid):
        """."""
        loans = cls.get_pendings_loans(library_pid)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid')
            item = Item.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_SHELF and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan

    @property
    def status(self):
        """Shortcut for item status."""
        return self.get('status', '')

    def reindex(self, forceindex=False):
        """Reindex record."""
        if forceindex:
            ItemsIndexer(version_type="external_gte").index(self)
        else:
            ItemsIndexer().index(self)

    def status_update(self, dbcommit=False, reindex=False, forceindex=False):
        """Update item status."""
        statuses = {
            'ITEM_ON_LOAN': 'on_loan',
            'ITEM_AT_DESK': 'at_desk',
            'ITEM_IN_TRANSIT_FOR_PICKUP': 'in_transit',
            'ITEM_IN_TRANSIT_TO_HOUSE': 'in_transit',
        }
        loan = get_loan_for_item(self.pid)
        if loan:
            self['status'] = statuses[loan.get('state')]
        else:
            if self['status'] != ItemStatus.MISSING:
                self['status'] = ItemStatus.ON_SHELF
        if dbcommit:
            self.commit()
            self.dbcommit(reindex=True, forceindex=True)

    @property
    def available(self):
        """Get availability for loan."""
        return (self.status == ItemStatus.ON_SHELF) and \
            self.number_of_requests() == 0

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

    def get_extension_count(self):
        """Get item renewal count."""
        loan = get_loan_for_item(self.pid)
        if loan:
            return loan.get('extension_count', 0)
        return 0

    def number_of_requests(self):
        """Get number of requests for a given item."""
        return len(list(self.get_requests()))

    def patron_request_rank(self, patron_barcode):
        """Get the rank of patron in list of requests on this item."""
        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            rank = 0
            requests = self.get_requests()
            for request in requests:
                rank += 1
                if request['patron_pid'] == patron.pid:
                    return rank
        return False

    def is_requested_by_patron(self, patron_barcode):
        """Check if the item is requested by a given patron."""
        patron = Patron.get_patron_by_barcode(patron_barcode)
        if patron:
            request = get_request_by_item_pid_by_patron_pid(
                item_pid=self.pid, patron_pid=patron.pid
            )
            if request:
                return True
        return False

    def is_loaned_to_patron(self, patron_barcode):
        """Check if the item is loaned by a given patron."""
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
        item = cls.get_record_by_pid(item_pid).replace_refs()
        if item:
            location_pid = item.get('location', {}).get('pid')
        return location_pid

    @add_loans_parameters_and_flush_indexes
    def validate_request(self, current_loan, **kwargs):
        """Validate item request."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='validate')
        )
        return self, {
            LoanAction.VALIDATE: loan
        }

    @add_loans_parameters_and_flush_indexes
    def extend_loan(self, current_loan, **kwargs):
        """Extend checkout duration for this item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='extend')
        )
        return self, {
            LoanAction.EXTEND: loan
        }

    @add_loans_parameters_and_flush_indexes
    def request(self, current_loan, **kwargs):
        """Request item for the user."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='request')
        )
        return self, {
            LoanAction.REQUEST: loan
        }

    @add_loans_parameters_and_flush_indexes
    def receive(self, current_loan, **kwargs):
        """Receive an item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='receive')
        )
        return self, {
            LoanAction.RECEIVE: loan
        }

    @add_loans_parameters_and_flush_indexes
    def checkin(self, current_loan, **kwargs):
        """Checkin a given item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkin')
        )
        return self, {
            LoanAction.CHECKIN: loan
        }

    @add_loans_parameters_and_flush_indexes
    def checkout(self, current_loan, **kwargs):
        """Checkout item to the user."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkout')
        )
        return self, {
            LoanAction.CHECKOUT: loan
        }

    @add_loans_parameters_and_flush_indexes
    def cancel_loan(self, current_loan, **kwargs):
        """Cancel a given item loan for a patron."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='cancel')
        )
        return self, {
            LoanAction.CANCEL: loan
        }

    def automatic_checkin(self):
        """Apply circ transactions for item."""
        if self.status == ItemStatus.ON_LOAN:
            loan_pid = self.get_loan_pid_with_item_on_loan(self.pid)
            return self.checkin(loan_pid=loan_pid)

        elif self.status == ItemStatus.IN_TRANSIT:
            loan_pid = self.get_loan_pid_with_item_in_transit(self.pid)
            return self.receive(loan_pid=loan_pid)

        elif self.status == ItemStatus.MISSING:
            return self.return_missing()

    def lose(self):
        """Lose the given item.

        This sets the status to ItemStatus.MISSING.
        All existing holdings will be canceled.
        """
        # cancel all actions if it is possible
        for loan in self.get_loans_by_item_pid(self.pid):
            loan_pid = loan['loan_pid']
            try:
                self.cancel_loan(loan_pid=loan_pid)
            except NoValidTransitionAvailable:
                pass
        self['status'] = ItemStatus.MISSING
        self.status_update(dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.LOSE: None
        }

    def return_missing(self):
        """Return the missing item.

        The item's status will be set to ItemStatus.ON_SHELF.
        """
        self['status'] = ItemStatus.ON_SHELF
        self.status_update(dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.RETURN_MISSING: None
        }
