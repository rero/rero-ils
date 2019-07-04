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

"""API for manipulating items."""

from datetime import datetime, timezone
from functools import partial, wraps

from flask import current_app
from invenio_circulation.api import get_loan_for_item, \
    patron_has_active_loan_on_item
from invenio_circulation.errors import MissingRequiredParameterError, \
    NoValidTransitionAvailableError
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_pid
from invenio_i18n.ext import current_i18n
from invenio_search import current_search

from .models import ItemIdentifier, ItemStatus
from ..api import IlsRecord, IlsRecordIndexer, IlsRecordsSearch
from ..documents.api import Document, DocumentsSearch
from ..errors import InvalidRecordID
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..loans.api import Loan, LoanAction, get_last_transaction_loc_for_item, \
    get_request_by_item_pid_by_patron_pid
from ..locations.api import Location
from ..minters import id_minter
from ..organisations.api import Organisation
from ..patrons.api import Patron, current_patron
from ..providers import Provider
from ..transactions.api import CircTransaction

# provider
ItemProvider = type(
    'ItemProvider',
    (Provider,),
    dict(identifier=ItemIdentifier, pid_type='item')
)
# minter
item_id_minter = partial(id_minter, provider=ItemProvider)
# fetcher
item_id_fetcher = partial(id_fetcher, provider=ItemProvider)


class ItemsIndexer(IlsRecordIndexer):
    """Indexing items in Elasticsearch."""

    def index(self, record):
        """Index an item."""
        return_value = super(ItemsIndexer, self).index(record)
        document_pid = record.replace_refs()['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        return return_value

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        return_value = super(ItemsIndexer, self).delete(record)
        document_pid = record.replace_refs()['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        return return_value


class ItemsSearch(IlsRecordsSearch):
    """ItemsSearch."""

    class Meta:
        """Search only on item index."""

        index = 'items'

    @classmethod
    def flush(cls):
        """Flush indexes."""
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        current_search.flush_and_refresh(cls.Meta.index)


def add_loans_parameters_and_flush_indexes(function):
    """Add missing action parameters."""
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        """Executed before loan action."""
        loan = None
        web_request = False
        patron_pid = kwargs.get('patron_pid')
        loan_pid = kwargs.get('loan_pid')
        # TODO: include in invenio-circulation
        if function.__name__ == 'request' and \
                not kwargs.get('pickup_location_pid'):
            raise MissingRequiredParameterError(
                description="Parameter 'pickup_location_pid' is required")

        if loan_pid:
            loan = Loan.get_record_by_pid(loan_pid)
        elif function.__name__ in ('checkout', 'request'):
            if function.__name__ == 'request' and not patron_pid:
                patron_pid = current_patron.pid
                web_request = True
            # create or get a loan
            if not patron_pid:
                raise MissingRequiredParameterError(
                    description="Parameter 'patron_pid' is required")
            if function.__name__ == 'checkout':
                request = get_request_by_item_pid_by_patron_pid(
                    item_pid=item.pid, patron_pid=patron_pid)
                if request:
                    loan = Loan.get_record_by_pid(request.get('loan_pid'))

            if not loan:
                data = {
                    'item_pid': item.pid,
                    'patron_pid': patron_pid
                }
                loan = Loan.create(data, dbcommit=True, reindex=True)
        else:
            raise MissingRequiredParameterError(
                description="Parameter 'loan_pid' is required")

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
                'transaction_location_pid',
                Patron.get_librarian_pickup_location_pid()
            )

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
    indexer = ItemsIndexer

    statuses = {
        'ITEM_ON_LOAN': 'on_loan',
        'ITEM_AT_DESK': 'at_desk',
        'ITEM_IN_TRANSIT_FOR_PICKUP': 'in_transit',
        'ITEM_IN_TRANSIT_TO_HOUSE': 'in_transit',
    }

    def dumps_for_circulation(self):
        """Enhance item information for api_views."""
        item = self.replace_refs()
        data = item.dumps()

        document = Document.get_record_by_pid(item['document']['pid'])
        doc_data = document.dumps()
        data['document']['title'] = doc_data['title']

        location = Location.get_record_by_pid(item['location']['pid'])
        loc_data = location.dumps()
        data['location']['name'] = loc_data['name']
        data['actions'] = list(self.actions)
        data['available'] = self.available
        # data['number_of_requests'] = self.number_of_requests()
        for loan in self.get_requests():
            data.setdefault('pending_loans',
                            []).append(loan.dumps_for_circulation())

        return data

    @classmethod
    def get_document_pid_by_item_pid(cls, item_pid):
        """Returns document pid from item pid."""
        item = cls.get_record_by_pid(item_pid).replace_refs()
        return item.get('document', {}).get('pid')

    @classmethod
    def get_items_pid_by_document_pid(cls, document_pid):
        """Returns item pisd from document pid."""
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
        """Returns loan pid for checked out item."""
        search = search_by_pid(
            item_pid=item_pid, filter_states=['ITEM_ON_LOAN'])
        results = search.source(['loan_pid']).scan()
        try:
            return next(results).loan_pid
        except StopIteration:
            return None

    @classmethod
    def get_loan_pid_with_item_in_transit(cls, item_pid):
        """Returns loan pi for in_transit item."""
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
        """Returns list of pending loand for a given library."""
        # check library exists
        lib = Library.get_record_by_pid(library_pid)
        if not lib:
            raise Exception('Invalid Library PID')

        results = current_circulation.loan_search\
            .source(['loan_pid'])\
            .params(preserve_order=True)\
            .filter('term', state='PENDING')\
            .filter('term', library_pid=library_pid)\
            .sort({'transaction_date': {'order': 'asc'}})\
            .scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.loan_pid)

    @classmethod
    def get_checked_out_loans(cls, patron_pid):
        """Returns checked out loans for a given patron."""
        # check library exists
        patron = Patron.get_record_by_pid(patron_pid)
        if not patron:
            raise InvalidRecordID('Invalid Patron PID')
        results = current_circulation.loan_search\
            .source(['loan_pid'])\
            .params(preserve_order=True)\
            .filter('term', state='ITEM_ON_LOAN')\
            .filter('term', patron_pid=patron_pid)\
            .sort({'transaction_date': {'order': 'asc'}})\
            .scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.loan_pid)

    @classmethod
    def get_checked_out_items(cls, patron_pid):
        """Return checked out items for a given patron."""
        loans = cls.get_checked_out_loans(patron_pid)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid')
            item = Item.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_LOAN and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan

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
        """Returns list of requests to validate for a given library."""
        loans = cls.get_pendings_loans(library_pid)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid')
            item = Item.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_SHELF and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan

    def get_organisation(self):
        """Shortcut to the organisation of the item location."""
        return self.get_library().get_organisation()

    def get_library(self):
        """Shortcut to the library of the item location."""
        return self.get_location().get_library()

    def get_location(self):
        """Shortcut to the location of the item."""
        location_pid = self.replace_refs()['location']['pid']
        return Location.get_record_by_pid(location_pid)

    def get_library_of_last_location(self):
        """Returns the library record of the circulation transaction location.

        of the last loan.
        """
        return self.get_last_location().get_library()

    def get_last_location(self):
        """Returns the location record of the transaction location.

        of the last loan.
        """
        location_pid = self.last_location_pid
        return Location.get_record_by_pid(location_pid)

    @property
    def status(self):
        """Shortcut for item status."""
        return self.get('status', '')

    @property
    def item_type_pid(self):
        """Shortcut for item type pid."""
        item_type_pid = self.replace_refs()['item_type']['pid']
        return item_type_pid

    @property
    def location_pid(self):
        """Shortcut for item location pid."""
        location_pid = self.replace_refs()['location']['pid']
        return location_pid

    @property
    def library_pid(self):
        """Shortcut for item library pid."""
        location = Location.get_record_by_pid(self.location_pid).replace_refs()
        return location.get('library').get('pid')

    @property
    def last_location_pid(self):
        """Returns the location pid of the circulation transaction location.

        of the last loan.
        """
        loan_location_pid = get_last_transaction_loc_for_item(self.pid)
        if loan_location_pid and Location.get_record_by_pid(loan_location_pid):
            return loan_location_pid
        return self.location_pid

    def action_filter(self, action, loan):
        """Filter actions."""
        from ..circ_policies.api import CircPolicy
        from ..loans.utils import extend_loan_data_is_valid
        patron_pid = loan.get('patron_pid')
        patron_type_pid = Patron.get_record_by_pid(
            patron_pid).patron_type_pid
        circ_policy = CircPolicy.provide_circ_policy(
                self.library_pid,
                patron_type_pid,
                self.item_type_pid
        )
        data = {
            'action_validated': True,
            'new_action': None
        }
        if action == 'extend':
            extension_count = loan.get('extension_count', 0)
            if not (
                circ_policy.get('number_renewals') > 0 and
                extension_count < circ_policy.get('number_renewals') and
                extend_loan_data_is_valid(
                    loan.get('end_date'),
                    circ_policy.get('renewal_duration'),
                    self.library_pid
                )
            ) or self.number_of_requests():
                data['action_validated'] = False
        if action == 'checkout':
            if not circ_policy.get('allow_checkout'):
                data['action_validated'] = False

        if action == 'receive':
            if (
                circ_policy.get('allow_checkout') and
                loan.get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP' and
                loan.get('patron_pid') == patron_pid
            ):
                data['action_validated'] = False
                data['new_action'] = 'checkout'
        return data

    @property
    def actions(self):
        """Get all available actions."""
        transitions = current_app.config.get('CIRCULATION_LOAN_TRANSITIONS')
        loan = get_loan_for_item(self.pid)
        actions = set()
        if loan:
            for transition in transitions.get(loan.get('state')):
                action = transition.get('trigger')
                data = self.action_filter(action, loan)
                if data.get('action_validated'):
                    actions.add(action)
                if data.get('new_action'):
                    actions.add(data.get('new_action'))
        # default actions
        if not loan:
            for transition in transitions.get('CREATED'):
                action = transition.get('trigger')
                actions.add(action)
        # remove unsupported action
        for action in ['cancel', 'request']:
            try:
                actions.remove(action)
                # not yet supported
                # actions.add('cancel_loan')
            except KeyError:
                pass
        # rename
        try:
            actions.remove('extend')
            actions.add('extend_loan')
        except KeyError:
            pass
        # if self['status'] == ItemStatus.MISSING:
        #     actions.add('return_missing')
        # else:
        #     actions.add('lose')
        return actions

    def status_update(self, dbcommit=False, reindex=False, forceindex=False):
        """Update item status."""
        loan = get_loan_for_item(self.pid)
        if loan:
            self['status'] = self.statuses[loan.get('state')]
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

    def get_item_end_date(self):
        """Get item due date for a given item."""
        loan = get_loan_for_item(self.pid)
        if loan:
            end_date = loan['end_date']
            # due_date = datetime.strptime(end_date, '%Y-%m-%d')
            from ...filter import format_date_filter

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
        """Get item selflocation or the transaction location of the.

        last loan.
        """
        # TODO: for requests we probably need the transation_location_pid
        #       to deal with multiple pickup locations for a library
        item = cls.get_record_by_pid(item_pid)
        if item:
            library = item.get_library_of_last_location()
            return library.get_pickup_location_pid()

    @add_loans_parameters_and_flush_indexes
    def validate_request(self, current_loan, **kwargs):
        """Validate item request."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='validate_request')
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
        """Request item for the user and create notifications."""
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
        actions = {LoanAction.CHECKIN: loan}
        requests = self.number_of_requests()
        if requests:
            request = next(self.get_requests())
            requested_loan = Loan.get_record_by_pid(request.get('loan_pid'))
            pickup_location_pid = requested_loan.get('pickup_location_pid')
            if self.last_location_pid == pickup_location_pid:
                if loan.is_active:
                    item, cancel_action = self.cancel_loan(
                        loan_pid=loan.get('loan_pid'))
            item, validate_action = self.validate_request(**request)
        return self, actions

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

    def get_owning_pickup_location_pid(self):
        """Returns the pickup location for the item owning location."""
        library = self.get_library()
        return library.get_pickup_location_pid()

    def automatic_checkin(self):
        """Apply circ transactions for item."""
        if self.status == ItemStatus.ON_LOAN:
            loan_pid = self.get_loan_pid_with_item_on_loan(self.pid)
            return self.checkin(loan_pid=loan_pid)

        elif self.status == ItemStatus.IN_TRANSIT:
            do_receive = False
            loan_pid = self.get_loan_pid_with_item_in_transit(self.pid)
            loan = Loan.get_record_by_pid(loan_pid)
            transaction_location_pid = \
                Patron.get_librarian_pickup_location_pid()
            if loan['state'] == 'ITEM_IN_TRANSIT_FOR_PICKUP' and \
                    loan['pickup_location_pid'] == transaction_location_pid:
                do_receive = True
            if loan['state'] == 'ITEM_IN_TRANSIT_TO_HOUSE' and \
                    self.get_owning_pickup_location_pid() \
                    == transaction_location_pid:
                do_receive = True
            if do_receive:
                return self.receive(loan_pid=loan_pid)
            return self, {
                LoanAction.NO: None
            }

        elif self.status == ItemStatus.MISSING:
            return self.return_missing()
        return self, {
            LoanAction.NO: None
        }

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
            except NoValidTransitionAvailableError:
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

    def get_number_of_loans(self):
        """Get number of loans."""
        search = search_by_pid(
            item_pid=self.pid,
            exclude_states=[
                'CANCELLED',
                'ITEM_RETURNED',
            ]
        )
        results = search.source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        loans = self.get_number_of_loans()
        if loans:
            links['loans'] = loans
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    @property
    def organisation_pid(self):
        """Get organisation pid for item."""
        library = Library.get_record_by_pid(self.library_pid)
        return library.organisation_pid

    @property
    def organisation_view(self):
        """Get Organisation view for item."""
        organisation = Organisation.get_record_by_pid(self.organisation_pid)
        return organisation['view_code']
