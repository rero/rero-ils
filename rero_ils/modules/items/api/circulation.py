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
from ...errors import InvalidRecordID, NoCirculationAction
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
        elif function.__name__ == 'validate_request':
            # we arent allowed to validate a request on items with no requests.
            raise NoCirculationAction(
                'No circulation action is possible')
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

        if function.__name__ == 'validate_request' and loan_pid:
            # no item validation is possible when an item has an active loan.
            loans = item.get_loans_states_by_item_pid_exclude_loan_pid(
                item.pid, loan_pid)
            states = current_app.config['CIRCULATION_STATES_LOAN_ACTIVE']
            for state in loans:
                if state in states:
                    raise NoValidTransitionAvailableError()

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


def add_checkin_parameters_and_flush_indexes(function):
    """Add missing checkin action parameters."""
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        """Executed before loan action."""
        from . import ItemsSearch
        loan = None
        loan_pid = kwargs.get('pid')
        loans_list = item.get_loan_states_for_an_item()
        if loan_pid:
            loan = Loan.get_record_by_pid(loan_pid)
        if not loans_list:
            # CHECKIN_1_1: item on_shelf, no pending loans.
            item.checkin_on_shelf(loans_list, **kwargs)
        elif (LoanState.ITEM_AT_DESK not in loans_list and
              LoanState.ITEM_ON_LOAN not in loans_list):
            if LoanState.ITEM_IN_TRANSIT_FOR_PICKUP in loans_list:
                # CHECKIN_4: item in_transit (IN_TRANSIT_FOR_PICKUP)
                loan, kwargs = item.checkin_in_transit_for_pickup(**kwargs)
            elif LoanState.ITEM_IN_TRANSIT_TO_HOUSE in loans_list:
                # CHECKIN_5: item in_transit (IN_TRANSIT_TO_HOUSE)
                loan, kwargs = item.checkin_in_transit_to_house(
                    loans_list, **kwargs)
            elif LoanState.PENDING in loans_list:
                # CHECKIN_1_2_1: item on_shelf, with pending loans.
                loan, kwargs = item.validate_first_pending_request(**kwargs)
        elif LoanState.ITEM_AT_DESK in loans_list:
            # CHECKIN_2: item at_desk
            item.checkin_at_desk(**kwargs)
        elif LoanState.ITEM_ON_LOAN in loans_list:
            # CHECKIN_3: item on_loan, will be checked-in normally.
            loan = item.get_first_loan_by_state(state=LoanState.ITEM_ON_LOAN)

        kwargs = item.complete_missing_params(loan, **kwargs)

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

    def checkin_on_shelf(self, loans_list, **kwargs):
        """Checkin actions for an item on_shelf.

        :param item : the item record
        :param loans_list: list of loans states attached to the item
        :param kwargs : all others named arguments
        """
        # CHECKIN_1_1: item on_shelf, no pending loans.
        libraries = self.compare_item_pickup_transaction_libraries(**kwargs)
        transaction_item_libraries = libraries['transaction_item_libraries']
        if transaction_item_libraries:
            # CHECKIN_1_1_1, item library = transaction library
            # item will be checked in in home library, no action
            raise NoCirculationAction(
                'No circulation action performed')
        else:
            # CHECKIN_1_1_2: item library != transaction library
            # item will be checked-in in an external library, no
            # circulation action performed, add item status in_transit
            self['status'] == ItemStatus.IN_TRANSIT
            self.status_update(
                dbcommit=True, reindex=True, forceindex=True)
            raise NoCirculationAction('in_transit status added')

    def checkin_at_desk(self, **kwargs):
        """Checkin actions for at_desk item.

        :param item : the item record
        :param kwargs : all others named arguments
        """
        # CHECKIN_2: item at_desk
        at_desk_loan = self.get_first_loan_by_state(
            state=LoanState.ITEM_AT_DESK)
        kwargs['pickup_location_pid'] = \
            at_desk_loan['pickup_location_pid']
        libraries = self.compare_item_pickup_transaction_libraries(**kwargs)
        if libraries['transaction_pickup_libraries']:
            # CHECKIN_2_1: pickup location = transaction library
            # (no action, item is: at_desk (ITEM_AT_DESK))
            raise NoCirculationAction(
                'No circulation action performed')
        else:
            # CHECKIN_2_2: pickup location != transaction library
            # item is: in_transit
            at_desk_loan['state'] == 'IN_TRANSIT_FOR_PICKUP'
            at_desk_loan.update(
                at_desk_loan, dbcommit=True, reindex=True)
            self['status'] == ItemStatus.IN_TRANSIT
            self.status_update(
                dbcommit=True, reindex=True, forceindex=True)
            raise NoCirculationAction(
                'in_transit status added')

    def checkin_in_transit_for_pickup(self, **kwargs):
        """Checkin actions for item in_transit for pickup.

        :param item : the item record
        :param kwargs : all others named arguments
        """
        # CHECKIN_4: item in_transit (IN_TRANSIT_FOR_PICKUP)
        in_transit_loan = self.get_first_loan_by_state(
            state=LoanState.ITEM_IN_TRANSIT_FOR_PICKUP)
        kwargs['pickup_location_pid'] = \
            in_transit_loan['pickup_location_pid']
        libraries = self.compare_item_pickup_transaction_libraries(**kwargs)
        if libraries['transaction_pickup_libraries']:
            # CHECKIN_4_1: pickup location = transaction library
            # (delivery_receive current loan, item is: at_desk(ITEM_AT_DESK))
            kwargs['receive_in_transit_request'] = True
            loan = in_transit_loan
            return loan, kwargs
        else:
            # CHECKIN_4_2: pickup location != transaction library
            # (no action, item is: in_transit (IN_TRANSIT_FOR_PICKUP))
            raise NoCirculationAction(
                'No circulation action performed')

    def checkin_in_transit_to_house(
            self, loans_list, **kwargs):
        """Checkin actions for an item in IN_TRANSIT_TO_HOUSE with no requests.

        :param item : the item record
        :param loans_list: list of loans states attached to the item
        :param kwargs : all others named arguments
        """
        # CHECKIN_5: item in_transit (IN_TRANSIT_TO_HOUSE)
        libraries = self.compare_item_pickup_transaction_libraries(**kwargs)
        transaction_item_libraries = libraries['transaction_item_libraries']
        in_transit_loan = self.get_first_loan_by_state(
            state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE)
        if LoanState.PENDING not in loans_list:
            # CHECKIN_5_1: item has no pending loans
            if transaction_item_libraries:
                # CHECKIN_5_1_1: item location = transaction library
                # (house_receive current loan, item is: on_shelf)
                kwargs['receive_in_transit_request'] = True
                loan = in_transit_loan
            else:
                # CHECKIN_5_1_2: item location != transaction library
                # (no action, item is: in_transit (IN_TRANSIT_TO_HOUSE))
                raise NoCirculationAction(
                    'No circulation action performed')
        else:
            # CHECKIN_5_2: item has pending requests.
            loan, kwargs = self.checkin_in_transit_to_house_with_requests(
                in_transit_loan, **kwargs)
        return loan, kwargs

    def checkin_in_transit_to_house_with_requests(
            self, in_transit_loan, **kwargs):
        """Checkin actions for an item in IN_TRANSIT_TO_HOUSE with requests.

        :param item : the item record
        :param in_transit_loan: the in_transit loan attached to the item
        :param kwargs : all others named arguments
        """
        # CHECKIN_5_2: pending loan exists.
        pending = self.get_first_loan_by_state(state=LoanState.PENDING)
        if pending:
            pending_params = kwargs
            pending_params['pickup_location_pid'] = \
                pending['pickup_location_pid']
            libraries = self.compare_item_pickup_transaction_libraries(
                **kwargs)
            if libraries['transaction_pickup_libraries']:
                # CHECKIN_5_2_1_1: pickup location of first PENDING loan = item
                # library (house_receive current loan, item is: at_desk
                # [automatic validate first PENDING loan]
                if libraries['item_pickup_libraries']:
                    kwargs['receive_current_and_validate_first'] = True
                    loan = in_transit_loan
                else:
                    # CHECKIN_5_2_1_2: pickup location of first PENDING loan !=
                    # item library (cancel current loan, item is: at_desk
                    # automatic validate first PENDING loan
                    kwargs['cancel_current_and_receive_first'] = True
                    loan = in_transit_loan
            else:
                # CHECKIN_5_2_2: pickup location of first PENDING loan !=
                # transaction library
                if libraries['item_pickup_libraries']:
                    # CHECKIN_5_2_2_1: pickup location of first PENDING loan =
                    # item library (no action, item is: in_transit)
                    raise NoCirculationAction(
                        'No circulation action performed')
                else:
                    # CHECKIN_5_2_2_2: pickup location of first PENDING loan !=
                    # item library (checkin current loan, item is: in_transit)
                    # [automatic cancel current, automatic validate first loan]
                    kwargs['cancel_current_and_receive_first'] = True
                    loan = in_transit_loan
        return loan, kwargs

    def validate_first_pending_request(self, **kwargs):
        """Checkin actions for item at_desk with pending loans.

        :param item : the item record
        :param kwargs : all others named arguments
        """
        # CHECKIN_1_2_1: item on_shelf, with pending loans.
        pending = self.get_first_loan_by_state(state=LoanState.PENDING)
        if pending:
            # validate the first pending request.
            kwargs['validate_current_loan'] = True
            loan = pending
        return loan, kwargs

    def complete_missing_params(self, loan, **kwargs):
        """Complete the missing parameters to start the checkin action.

        :param item : the item record
        :param loan: the item loan to be used for the checkin action
        :param kwargs : all others named arguments
        """
        # set missing parameters
        kwargs['item_pid'] = item_pid_to_object(self.pid)
        kwargs['patron_pid'] = loan.get('patron_pid')
        kwargs['pid'] = loan.pid
        # TODO: case when user want to have his own transaction date
        kwargs['transaction_date'] = datetime.now(timezone.utc).isoformat()
        if not kwargs.get('transaction_user_pid'):
            kwargs.setdefault(
                'transaction_user_pid', current_patron.pid)
        kwargs.setdefault(
            'document_pid', self.replace_refs().get('document', {}).get('pid'))
        return kwargs

    def compare_item_pickup_transaction_libraries(self, **kwargs):
        """Compare item library, pickup and transaction libraries.

        :param kwargs : all others named arguments
        :return a dict comparison with the following True or False keys
            transaction_item_libraries: between transaction and item
            transaction_pickup_libraries: between transaction and pickup
            item_pickup_libraries: between item and pickup
        """
        data = {
            'transaction_item_libraries': False,
            'transaction_pickup_libraries': False,
            'item_pickup_libraries': False
        }
        # TODO: better coding needed here, some lines will be merged
        transaction_location_pid = kwargs.pop('transaction_location_pid', None)
        transaction_library_pid = kwargs.pop('transaction_library_pid', None)

        if not transaction_library_pid:
            transaction_library_pid = Location.get_record_by_pid(
                transaction_location_pid).library_pid

        pickup_location_pid = kwargs.pop('pickup_location_pid', None)
        pickup_library_pid = kwargs.pop(
            'pickup_library_pid', None)
        if not pickup_library_pid:
            if not pickup_location_pid:
                pickup_library_pid = transaction_library_pid
            else:
                pickup_library_pid = Location.get_record_by_pid(
                    pickup_location_pid).library_pid

        if self.library_pid == pickup_library_pid:
            data['item_pickup_libraries'] = True
        if self.library_pid == transaction_library_pid:
            data['transaction_item_libraries'] = True
        if pickup_library_pid == transaction_library_pid:
            data['transaction_pickup_libraries'] = True
        return data

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

    def checkin_validate_current_loan(self, actions, **kwargs):
        """Validate the current loan.

        :param actions : dict the list of actions performed
        :param kwargs : all others named arguments
        :return:  the item record and list of actions performed
        """
        validate_current_loan = kwargs.pop('validate_current_loan', None)
        if validate_current_loan:
            item, validate_actions = self.validate_request(**kwargs)
            actions = {LoanAction.VALIDATE: validate_actions}
            actions.update(validate_actions)
            return item, actions
        return self, actions

    def actions_after_a_checkin(self, checkin_loan, actions, **kwargs):
        """Actions executed after a checkin.

        :param checkin_loan : the checked-in loan
        :param actions : dict the list of actions performed
        :param kwargs : all others named arguments
        :return:  the item record and list of actions performed
        """
        # if item is requested we will automatically:
        # - cancel the checked-in loan if still active
        # - validate the next request
        requests = self.number_of_requests()
        if requests:
            request = next(self.get_requests())
            if checkin_loan.is_active:
                params = kwargs
                params['pid'] = checkin_loan.pid
                item, cancel_actions = self.cancel_loan(**params)
                actions.update(cancel_actions)
            # pass the correct transaction location
            transaction_loc_pid = checkin_loan.get(
                'transaction_location_pid')
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
            return item, actions
        return self, actions

    def receive_in_transit_current_loan(self, actions, **kwargs):
        """Receive the item_in_transit_for_pickup loan.

        :param actions : dict the list of actions performed
        :param kwargs : all others named arguments
        :return: the item record and list of actions performed
        """
        receive_in_transit_request = kwargs.pop(
            'receive_in_transit_request', None)
        if receive_in_transit_request:
            item, receive_action = self.receive(**kwargs)
            actions.update(receive_action)
            # receive_loan = receive_action[LoanAction.RECEIVE]
            return item, actions
        return self, actions

    def receive_and_validate_requests(self, actions, **kwargs):
        """Receive the item_in_transit_in_house and validate first loan.

        :param actions : dict the list of actions performed
        :param kwargs : all others named arguments
        :return: the item record and list of actions performed
        """
        receive_current_and_validate_first = kwargs.pop(
            'receive_current_and_validate_first', None)
        if receive_current_and_validate_first:
            item, receive_action = self.receive(**kwargs)
            actions.update(receive_action)
            receive_loan = receive_action[LoanAction.RECEIVE]
            # validate first request
            requests = item.number_of_requests()
            if requests:
                request = next(item.get_requests())
                if receive_loan.is_active:
                    params = kwargs
                    params['pid'] = receive_loan.pid
                    item, cancel_actions = item.cancel_loan(**params)
                    actions.update(cancel_actions)
                # pass the correct transaction location
                transaction_loc_pid = receive_loan.get(
                    'transaction_location_pid')
                request['transaction_location_pid'] = transaction_loc_pid
                # validate the request
                item, validate_actions = item.validate_request(**request)
                actions.update(validate_actions)
                validate_loan = validate_actions[LoanAction.VALIDATE]
                # receive request if it is requested at transaction library
                if validate_loan['state'] == \
                        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                    trans_loc = Location.get_record_by_pid(
                        transaction_loc_pid)
                    req_loc = Location.get_record_by_pid(
                        request.get('pickup_location_pid'))
                    if req_loc.library_pid == trans_loc.library_pid:
                        item, receive_action = item.receive(**request)
                        actions.update(receive_action)
            return item, actions
        return self, actions

    def cancel_and_receive_first_loan(self, current_loan, actions, **kwargs):
        """Cancel the current loan and receive the first request.

        :param current_loan : loan to cancel
        :param actions : dict the list of actions performed
        :param kwargs : all others named arguments
        :return: the item record and list of actions performed
        """
        cancel_current_and_receive_first = kwargs.pop(
            'cancel_current_and_receive_first', None)
        if cancel_current_and_receive_first:
            params = kwargs
            params['pid'] = current_loan.pid
            item, cancel_actions = self.cancel_loan(**params)
            actions.update(cancel_actions)
            cancel_loan = cancel_actions[LoanAction.CANCEL]
            # receive the first request
            requests = item.number_of_requests()
            if requests:
                request = next(item.get_requests())
                # pass the correct transaction location
                transaction_loc_pid = cancel_loan.get(
                    'transaction_location_pid')
                request['transaction_location_pid'] = transaction_loc_pid
                # validate the request
                item, validate_actions = item.validate_request(**request)
                actions.update(validate_actions)
                validate_loan = validate_actions[LoanAction.VALIDATE]
                # receive request if it is requested at transaction library
                if validate_loan['state'] == \
                        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                    trans_loc = Location.get_record_by_pid(
                        transaction_loc_pid)
                    req_loc = Location.get_record_by_pid(
                        request.get('pickup_location_pid'))
                    if req_loc.library_pid == trans_loc.library_pid:
                        item, receive_action = item.receive(**request)
                        actions.update(receive_action)
            return item, actions
        return self, actions

    @add_checkin_parameters_and_flush_indexes
    def checkin(self, current_loan, **kwargs):
        """Perform a smart checkin action."""
        actions = {}
        # checkin actions for an item on_shelf
        item, actions = self.checkin_validate_current_loan(actions, **kwargs)
        if actions:
            return item, actions
        # checkin actions for an item in_transit with no requests
        item, actions = self.receive_in_transit_current_loan(actions, **kwargs)
        if actions:
            return item, actions
        # checkin actions for an item in_transit_to_house at home library
        item, actions = self.receive_and_validate_requests(actions, **kwargs)
        if actions:
            return item, actions
        # checkin actions for an item in_transit_to_house at external library
        item, actions = self.cancel_and_receive_first_loan(
            current_loan, actions, **kwargs)
        if actions:
            return item, actions
        # standard checkin actions
        checkin_loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='checkin')
        )
        actions = {LoanAction.CHECKIN: checkin_loan}
        # validate and receive actions to execute after a standard checkin
        item, actions = self.actions_after_a_checkin(
            checkin_loan, actions, **kwargs)
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
    def get_loans_states_by_item_pid_exclude_loan_pid(cls, item_pid, loan_pid):
        """Return list of loan states for an item excluding a given loan.

        :param item_pid : the item pid
        :param loan_pid : the loan pid to exclude
        :return:  the list of loans states attached to the item
        """
        item_pid_object = item_pid_to_object(item_pid)
        results = current_circulation.loan_search_cls()\
            .filter('term', item_pid__value=item_pid_object['value'])\
            .filter('term', item_pid__type=item_pid_object['type'])\
            .source(includes='pid').scan()
        return [Loan.get_record_by_pid(loan.pid)['state']
                for loan in results if loan.pid != loan_pid]

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

    def get_first_loan_by_state(self, state=None):
        """Return the first loan with the given state and attached to item.

        :param state : the loan state
        :return: first loan found
        """
        return list(self.get_item_loans_by_state(state=state))[0]

    def get_item_loans_by_state(self, state=None, sort_by=None):
        """Return sorted item loans with a given state.

        default sort is transaction_date.
        :param state : the loan state
        :param sort_by : field to use for sorting
        :return: loans found
        """
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid), filter_states=[
                state
            ]).params(preserve_order=True).source(['pid'])
        order_by = 'asc'
        sort_by = sort_by or 'transaction_date'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'
        search = search.sort({sort_by: {'order': order_by}})
        for result in search.scan():
            yield Loan.get_record_by_pid(result.pid)

    def get_loan_states_for_an_item(self):
        """Return list of all the loan states attached to the item.

        :return: list of all loan states attached to the item
        """
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid), filter_states=[
                LoanState.PENDING,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
                LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
                LoanState.ITEM_AT_DESK,
                LoanState.ITEM_ON_LOAN
            ]).params(preserve_order=True).source(['state'])
        return list(dict.fromkeys([result.state for result in search.scan()]))

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
