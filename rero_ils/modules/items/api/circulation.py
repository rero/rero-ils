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

"""API for manipulating item circulation transactions."""

from datetime import datetime, timezone
from functools import wraps

from flask import current_app
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.errors import MissingRequiredParameterError, \
    NoValidTransitionAvailableError
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item_or_document, \
    search_by_pid
from invenio_i18n.ext import current_i18n
from invenio_pidstore.errors import PersistentIdentifierError
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search

from ..models import ItemCirculationAction, ItemStatus
from ..utils import item_pid_to_object
from ...api import IlsRecord
from ...circ_policies.api import CircPolicy
from ...documents.api import Document
from ...errors import InvalidRecordID
from ...libraries.api import Library
from ...loans.api import Loan, LoanAction, LoanState, \
    get_last_transaction_loc_for_item, get_request_by_item_pid_by_patron_pid
from ...locations.api import Location
from ...patrons.api import Patron, current_patron
from ....filter import format_date_filter


def add_loans_parameters_and_flush_indexes(function):
    """Add missing action parameters."""
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        """Executed before loan action."""
        from . import ItemsSearch
        loan = None
        web_request = False
        patron_pid = kwargs.get('patron_pid')
        loan_pid = kwargs.get('pid')
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
                    loan = Loan.get_record_by_pid(request.get('pid'))

            if not loan:
                data = {
                    'item_pid': item_pid_to_object(item.pid),
                    'patron_pid': patron_pid
                }
                loan = Loan.create(data, dbcommit=True, reindex=True)
        else:
            raise MissingRequiredParameterError(
                description="Parameter 'pid' is required")

        # set missing parameters
        kwargs['item_pid'] = item_pid_to_object(item.pid)
        kwargs['patron_pid'] = loan.get('patron_pid')
        kwargs['pid'] = loan.pid
        # TODO: case when user want to have his own transaction date
        kwargs['transaction_date'] = datetime.now(timezone.utc).isoformat()
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
            current_circulation.loan_search_cls.Meta.index)
        item.status_update(dbcommit=True, reindex=True, forceindex=True)
        ItemsSearch.flush()
        return item, action_applied
    return wrapper


class ItemCirculation(IlsRecord):
    """Item circulation class."""

    statuses = {
        LoanState.ITEM_ON_LOAN: 'on_loan',
        LoanState.ITEM_AT_DESK: 'at_desk',
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP: 'in_transit',
        LoanState.ITEM_IN_TRANSIT_TO_HOUSE: 'in_transit',
    }

    @add_loans_parameters_and_flush_indexes
    def checkout(self, current_loan, **kwargs):
        """Checkout item to the user."""
        action_params, actions = self.prior_checkout_actions(kwargs)
        loan = Loan.get_record_by_pid(action_params.get('pid'))
        current_loan = loan or Loan.create(action_params,
                                           dbcommit=True,
                                           reindex=True)

        loan = current_circulation.circulation.trigger(
            current_loan, **dict(action_params, trigger='checkout')
        )
        actions.update({LoanAction.CHECKOUT: loan})
        return self, actions

    @add_loans_parameters_and_flush_indexes
    def cancel_loan(self, current_loan, **kwargs):
        """Cancel a given item loan for a patron."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='cancel')
        )
        return self, {
            LoanAction.CANCEL: loan
        }

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
        checkin_loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkin')
        )
        # to return the list of all applied actions
        actions = {LoanAction.CHECKIN: checkin_loan}
        # if item is requested we will automatically:
        # - cancel the checked-in loan if still active
        # - validate the next request
        requests = self.number_of_requests()
        if requests:
            request = next(self.get_requests())
            if checkin_loan.is_active:
                item, cancel_actions = self.cancel_loan(pid=checkin_loan.pid)
                actions.update(cancel_actions)
            # pass the correct transaction location
            transaction_loc_pid = checkin_loan.get('transaction_location_pid')
            request['transaction_location_pid'] = transaction_loc_pid
            # validate the request
            item, validate_actions = self.validate_request(**request)
            actions.update(validate_actions)
            validate_loan = validate_actions[LoanAction.VALIDATE]
            # receive the request if it is requested at transaction library
            if validate_loan['state'] == \
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                trans_loc = Location.get_record_by_pid(transaction_loc_pid)
                req_loc = Location.get_record_by_pid(
                    request.get('pickup_location_pid'))
                if req_loc.library_pid == trans_loc.library_pid:
                    item, receive_action = self.receive(**request)
                    actions.update(receive_action)
        return self, actions

    def prior_checkout_actions(self, action_params):
        """Actions executed prior to a checkout."""
        actions = {}
        if action_params.get('pid'):
            loan = Loan.get_record_by_pid(action_params.get('pid'))
            if (
                loan['state'] ==
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP and
                    loan.get('patron_pid') == action_params.get('patron_pid')
            ):
                item, receive_actions = self.receive(**action_params)
                actions.update(receive_actions)
            if loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE:
                item, cancel_actions = self.cancel_loan(pid=loan.get('pid'))
                actions.update(cancel_actions)
                del action_params['pid']
        else:
            loan = get_loan_for_item(item_pid_to_object(self.pid))
            if (loan and loan['state'] != LoanState.ITEM_AT_DESK):
                item, cancel_actions = self.cancel_loan(pid=loan.get('pid'))
                actions.update(cancel_actions)
        return action_params, actions

    def automatic_checkin(self, trans_loc_pid=None):
        """Apply circ transactions for item."""
        data = {}
        if trans_loc_pid is not None:
            data['transaction_location_pid'] = trans_loc_pid
        if self.status == ItemStatus.ON_LOAN:
            loan_pid = self.get_loan_pid_with_item_on_loan(self.pid)
            return self.checkin(pid=loan_pid, **data)

        elif self.status == ItemStatus.IN_TRANSIT:
            do_receive = False
            loan_pid = self.get_loan_pid_with_item_in_transit(self.pid)
            loan = Loan.get_record_by_pid(loan_pid)

            transaction_location_pid = trans_loc_pid
            if trans_loc_pid is None:
                transaction_location_pid = \
                    Patron.get_librarian_pickup_location_pid()
            if loan['state'] == \
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP and \
                    loan['pickup_location_pid'] == transaction_location_pid:
                do_receive = True
            if loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE:
                trans_loc = Location.get_record_by_pid(trans_loc_pid)
                if self.library_pid == trans_loc.library_pid:
                    do_receive = True
            if do_receive:
                return self.receive(pid=loan_pid, **data)
            return self, {
                # None action are available. Send anyway last known loan
                # informations.
                LoanAction.NO: loan
            }

        if self.status == ItemStatus.MISSING:
            return self.return_missing()
        return self, {
            LoanAction.NO: None
        }

    def dumps_for_circulation(self, sort_by=None):
        """Enhance item information for api_views."""
        item = self.replace_refs()
        data = item.dumps()

        document = Document.get_record_by_pid(item['document']['pid'])
        doc_data = document.dumps()
        data['document']['title'] = doc_data['title']

        location = Location.get_record_by_pid(item['location']['pid'])
        loc_data = location.dumps()
        data['location']['name'] = loc_data['name']
        organisation = self.get_organisation()
        data['location']['organisation'] = {
            'pid': organisation.get('pid'),
            'name': organisation.get('name')
        }
        data['actions'] = list(self.actions)
        data['available'] = self.available

        # data['number_of_requests'] = self.number_of_requests()
        for loan in self.get_requests(sort_by=sort_by):
            data.setdefault('pending_loans',
                            []).append(loan.dumps_for_circulation())
        return data

    @classmethod
    def get_loans_by_item_pid(cls, item_pid):
        """Return any loan loans for item."""
        item_pid_object = item_pid_to_object(item_pid)
        results = current_circulation.loan_search_cls()\
            .filter('term', item_pid__value=item_pid_object['value'])\
            .filter('term', item_pid__type=item_pid_object['type'])\
            .source(includes='pid').scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.pid)

    @classmethod
    def get_loan_pid_with_item_on_loan(cls, item_pid):
        """Returns loan pid for checked out item."""
        search = search_by_pid(item_pid=item_pid_to_object(
            item_pid), filter_states=[LoanState.ITEM_ON_LOAN])
        results = search.source(['pid']).scan()
        try:
            return next(results).pid
        except StopIteration:
            return None

    @classmethod
    def get_loan_pid_with_item_in_transit(cls, item_pid):
        """Returns loan pi for in_transit item."""
        search = search_by_pid(
            item_pid=item_pid_to_object(item_pid), filter_states=[
                "ITEM_IN_TRANSIT_FOR_PICKUP",
                "ITEM_IN_TRANSIT_TO_HOUSE"])
        results = search.source(['pid']).scan()
        try:
            return next(results).pid
        except StopIteration:
            return None

    @classmethod
    def get_pendings_loans(cls, library_pid=None, sort_by='transaction_date'):
        """Return list of sorted pending loans for a given library.

        default sort is set to transaction_date
        """
        # check if library exists
        lib = Library.get_record_by_pid(library_pid)
        if not lib:
            raise Exception('Invalid Library PID')
        # the '-' prefix means a desc order.
        sort_by = sort_by or 'transaction_date'
        order_by = 'asc'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'

        results = current_circulation.loan_search_cls()\
            .params(preserve_order=True)\
            .filter('term', state=LoanState.PENDING)\
            .filter('term', library_pid=library_pid)\
            .sort({sort_by: {"order": order_by}})\
            .source(includes='pid').scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.pid)

    @classmethod
    def get_checked_out_loans(
            cls, patron_pid=None, sort_by='transaction_date'):
        """Returns sorted checked out loans for a given patron."""
        # check library exists
        patron = Patron.get_record_by_pid(patron_pid)
        if not patron:
            raise InvalidRecordID('Invalid Patron PID')
        # the '-' prefix means a desc order.
        sort_by = sort_by or 'transaction_date'
        order_by = 'asc'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'

        results = current_circulation.loan_search_cls()\
            .params(preserve_order=True)\
            .filter('term', state=LoanState.ITEM_ON_LOAN)\
            .filter('term', patron_pid=patron_pid)\
            .sort({sort_by: {"order": order_by}})\
            .source(includes='pid').scan()
        for loan in results:
            yield Loan.get_record_by_pid(loan.pid)

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
    def last_location_pid(self):
        """Returns the location pid of the circulation transaction location.

        of the last loan.
        """
        loan_location_pid = get_last_transaction_loc_for_item(self.pid)
        if loan_location_pid and Location.get_record_by_pid(loan_location_pid):
            return loan_location_pid
        return self.location_pid

    # CIRCULATION METHODS =====================================================
    def can(self, action, **kwargs):
        """Check if a specific action is allowed on this item.

        :param action : the action to check as ItemCirculationAction part
        :param kwargs : all others named arguments useful to check
        :return a tuple with True|False to know if the action is possible and
                a list of reasons to disallow if False.
        """
        can, reasons = True, []
        actions = current_app.config.get('CIRCULATION_ACTIONS_VALIDATION', {})
        for func_name in actions.get(action, []):
            func_callback = obj_or_import_string(func_name)
            func_can, func_reasons = func_callback(self, **kwargs)
            reasons += func_reasons
            can = can and func_can
        return can, reasons

    @classmethod
    def can_request(cls, item, **kwargs):
        """Check if an item can be requested regarding the item status.

        :param item : the item to check.
        :param kwargs : other arguments.
        :return a tuple with True|False and reasons to disallow if False.
        """
        reasons = []
        if item.status in [ItemStatus.MISSING, ItemStatus.EXCLUDED]:
            reasons.append("Item status disallows the operation.")
        if 'patron' in kwargs:
            patron = kwargs['patron']
            if patron.organisation_pid != item.organisation_pid:
                reasons.append("Item and patron are not in the same "
                               "organisation.")
            if patron.get('barcode') and \
               item.is_loaned_to_patron(patron.get('barcode')):
                reasons.append("Item is already checked-out or requested by "
                               "patron.")
        return len(reasons) == 0, reasons

    @classmethod
    def can_extend(cls, item, **kwargs):
        """Checks if a patron has the rights to renew an item.

        :param item : the item to check.
        :param kwargs : additional arguments. To be relevant this method
                        require 'loan' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        from rero_ils.modules.loans.utils import extend_loan_data_is_valid
        if 'loan' not in kwargs:  # this method is not relevant
            return True, []
        loan = kwargs['loan']
        patron = Patron.get_record_by_pid(loan.get('patron_pid'))
        cipo = CircPolicy.provide_circ_policy(
            item.library_pid,
            patron.patron_type_pid,
            item.item_type_pid
        )
        extension_count = loan.get('extension_count', 0)
        if not (cipo.get('number_renewals') > 0 and
                extension_count < cipo.get('number_renewals') and
                extend_loan_data_is_valid(
                    loan.get('end_date'),
                    cipo.get('renewal_duration'),
                    item.library_pid
               )):
            return False, ['Circulation policies disallows the operation.']
        if item.number_of_requests():
            return False, ['A pending request exists on this item.']
        return True, []

    def action_filter(self, action, loan):
        """Filter actions."""
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
            can, reasons = self.can(ItemCirculationAction.EXTEND, loan=loan)
            if not can:
                data['action_validated'] = False
        if action == 'checkout':
            if not circ_policy.get('allow_checkout'):
                data['action_validated'] = False

        if action == 'receive':
            if (
                    circ_policy.get('allow_checkout') and
                    loan['state'] ==
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP and
                    loan.get('patron_pid') == patron_pid
            ):
                data['action_validated'] = False
                data['new_action'] = 'checkout'
        return data

    @property
    def actions(self):
        """Get all available actions."""
        transitions = current_app.config.get('CIRCULATION_LOAN_TRANSITIONS')
        loan = get_loan_for_item(item_pid_to_object(self.pid))
        actions = set()
        if loan:
            for transition in transitions.get(loan['state']):
                action = transition.get('trigger')
                data = self.action_filter(action, loan)
                if data.get('action_validated'):
                    actions.add(action)
                if data.get('new_action'):
                    actions.add(data.get('new_action'))
        # default actions
        if not loan:
            for transition in transitions.get(LoanState.CREATED):
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
        loan = get_loan_for_item(item_pid_to_object(self.pid))
        if loan:
            self['status'] = self.statuses[loan['state']]
        else:
            if self['status'] != ItemStatus.MISSING:
                self['status'] = ItemStatus.ON_SHELF
        if dbcommit:
            self.commit()
            self.dbcommit(reindex=True, forceindex=True)

    def item_has_active_loan_or_request(self):
        """Return True if active loan or a request found for item."""
        states = [LoanState.PENDING] + \
            current_app.config['CIRCULATION_STATES_LOAN_ACTIVE']
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid),
            filter_states=states,
        )
        search_result = search.execute()
        return search_result.hits.total

    def return_missing(self):
        """Return the missing item.

        The item's status will be set to ItemStatus.ON_SHELF.
        """
        # TODO: check transaction location
        self['status'] = ItemStatus.ON_SHELF
        self.status_update(dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.RETURN_MISSING: None
        }

    def get_number_of_loans(self):
        """Get number of loans."""
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid),
            exclude_states=[
                LoanState.CANCELLED,
                LoanState.ITEM_RETURNED,
            ]
        )
        results = search.source().count()
        return results

    def lose(self):
        """Lose the given item.

        This sets the status to ItemStatus.MISSING.
        All existing holdings will be canceled.
        """
        # cancel all actions if it is possible
        for loan in self.get_loans_by_item_pid(self.pid):
            loan_pid = loan['pid']
            try:
                self.cancel_loan(pid=loan_pid)
            except NoValidTransitionAvailableError:
                pass
        self['status'] = ItemStatus.MISSING
        self.status_update(dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.LOSE: None
        }

    def get_requests(self, sort_by=None):
        """Return sorted pending, item_on_transit, item_at_desk loans.

        default sort is transaction_date.
        """
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid), filter_states=[
                LoanState.PENDING,
                LoanState.ITEM_AT_DESK,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
            ]).params(preserve_order=True).source(['pid'])
        order_by = 'asc'
        sort_by = sort_by or 'transaction_date'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'
        search = search.sort({sort_by: {'order': order_by}})
        for result in search.scan():
            yield Loan.get_record_by_pid(result.pid)

    @property
    def available(self):
        """Get availability for item."""
        return self.item_has_active_loan_or_request() == 0

    def get_item_end_date(self, format='short'):
        """Get item due date for a given item."""
        loan = get_loan_for_item(item_pid_to_object(self.pid))
        if loan:
            end_date = loan['end_date']
            due_date = format_date_filter(
                end_date,
                date_format=format,
                locale=current_i18n.locale.language,
            )
            return due_date
        return None

    def get_extension_count(self):
        """Get item renewal count."""
        loan = get_loan_for_item(item_pid_to_object(self.pid))
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
            states = [LoanState.CREATED, LoanState.PENDING] + \
                current_app.config['CIRCULATION_STATES_LOAN_ACTIVE']
            search = search_by_patron_item_or_document(
                patron_pid=patron.pid,
                item_pid=item_pid_to_object(self.pid),
                document_pid=self.document_pid,
                filter_states=states,
            )
            search_result = search.execute()
            return search_result.hits.total > 0
        return False

    @classmethod
    def get_requests_to_validate(
            cls, library_pid=None, sort_by=None):
        """Returns list of requests to validate for a given library."""
        loans = cls.get_pendings_loans(
            library_pid=library_pid, sort_by=sort_by)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid', {}).get('value')
            item = cls.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_SHELF and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan

    @staticmethod
    def item_exists(item_pid):
        """Returns true if item exists for the given item_pid.

        :param item_pid: the item_pid object
        :type item_pid: object
        :return: True if item found otherwise False
        :rtype: bool
        """
        from .api import Item
        try:
            Item.get_record_by_pid(item_pid.get('value'))
        except PersistentIdentifierError:
            return False
        return True

    @classmethod
    def get_checked_out_items(cls, patron_pid=None, sort_by=None):
        """Return sorted checked out items for a given patron."""
        loans = cls.get_checked_out_loans(
            patron_pid=patron_pid, sort_by=sort_by)
        returned_item_pids = []
        for loan in loans:
            item_pid = loan.get('item_pid', {}).get('value')
            item = cls.get_record_by_pid(item_pid)
            if item.status == ItemStatus.ON_LOAN and \
                    item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield item, loan
