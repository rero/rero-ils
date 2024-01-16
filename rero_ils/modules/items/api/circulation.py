# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

from contextlib import suppress
from copy import deepcopy
from datetime import datetime

from flask import current_app
from flask_babel import gettext as _
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.errors import ItemNotAvailableError, \
    NoValidTransitionAvailableError
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import search_by_patron_item_or_document, \
    search_by_pid
from invenio_pidstore.errors import PersistentIdentifierError
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search

from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.patron_transactions.api import PatronTransactionsSearch

from .record import ItemRecord
from ..decorators import add_action_parameters_and_flush_indexes, \
    check_operation_allowed
from ..models import ItemCirculationAction, ItemIssueStatus, ItemStatus
from ..utils import item_pid_to_object
from ...circ_policies.api import CircPolicy
from ...errors import NoCirculationAction
from ...item_types.api import ItemType
from ...libraries.api import Library
from ...libraries.exceptions import LibraryNeverOpen
from ...loans.api import Loan, get_last_transaction_loc_for_item, \
    get_request_by_item_pid_by_patron_pid
from ...loans.models import LoanAction, LoanState
from ...locations.api import Location
from ...patrons.api import Patron
from ...utils import extracted_data_from_ref, sorted_pids
from ....filter import format_date_filter


class ItemCirculation(ItemRecord):
    """Item circulation class."""

    statuses = {
        LoanState.ITEM_ON_LOAN: 'on_loan',
        LoanState.ITEM_AT_DESK: 'at_desk',
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP: 'in_transit',
        LoanState.ITEM_IN_TRANSIT_TO_HOUSE: 'in_transit',
    }

    def change_status_commit_and_reindex(self):
        """Change item status after a successfull circulation action.

        Commits and reindex the item.
        This method is executed after every successfull circulation action.
        """
        current_search.flush_and_refresh(
            current_circulation.loan_search_cls.Meta.index)
        self.status_update(self, dbcommit=True, reindex=True, forceindex=True)

    def prior_validate_actions(self, **kwargs):
        """Check if the validate action can be executed or not."""
        if loan_pid := kwargs.get('pid'):
            # no item validation is possible when an item has an active loan.
            states = self.get_loans_states_by_item_pid_exclude_loan_pid(
                self.pid, loan_pid)
            active_states = current_app.config[
                'CIRCULATION_STATES_LOAN_ACTIVE']
            if set(active_states).intersection(states):
                raise NoValidTransitionAvailableError()
        else:
            # no validation is possible when loan is not found/given
            current_app.logger.error(
                'NoCirculationAction prior_validate_actions')
            raise NoCirculationAction(
                _('No circulation action performed: validate_actions'))

    def prior_extend_loan_actions(self, **kwargs):
        """Actions to execute before an extend_loan action."""
        loan_pid = kwargs.get('pid')
        checked_out = True  # we consider loan as checked-out
        if not loan_pid:
            loan = self.get_first_loan_by_state(LoanState.ITEM_ON_LOAN)
            if not loan:
                # item was not checked out
                checked_out = False
        else:
            loan = Loan.get_record_by_pid(loan_pid)

        # Check extend is allowed
        #   It's not allowed to extend an item if it is not checked out
        #   or has some pending requests already placed on it
        have_request = LoanState.PENDING in self.get_loan_states_for_an_item()
        if not checked_out or have_request:
            raise NoCirculationAction(
                _('No circulation action performed: extend_loan_actions'))

        return loan, kwargs

    def prior_checkin_actions(self, **kwargs):
        """Actions to execute before a smart checkin."""
        # TODO: find a better way to manage the different cases here.
        states = self.get_loan_states_for_an_item()
        if not states:
            # CHECKIN_1_1: item on_shelf, no pending loans.
            self.checkin_item_on_shelf(states, **kwargs)
        elif (LoanState.ITEM_AT_DESK not in states and
                LoanState.ITEM_ON_LOAN not in states):
            if LoanState.ITEM_IN_TRANSIT_FOR_PICKUP in states:
                # CHECKIN_4: item in_transit (IN_TRANSIT_FOR_PICKUP)
                loan, kwargs = self.checkin_item_in_transit_for_pickup(
                    **kwargs)
            elif LoanState.ITEM_IN_TRANSIT_TO_HOUSE in states:
                # CHECKIN_5: item in_transit (IN_TRANSIT_TO_HOUSE)
                loan, kwargs = self.checkin_item_in_transit_to_house(
                    states, **kwargs)
            elif LoanState.PENDING in states:
                # CHECKIN_1_2_1: item on_shelf, with pending loans.
                loan, kwargs = self.validate_item_first_pending_request(
                    **kwargs)
        elif LoanState.ITEM_AT_DESK in states:
            # CHECKIN_2: item at_desk
            self.checkin_item_at_desk(**kwargs)
        elif LoanState.ITEM_ON_LOAN in states:
            # CHECKIN_3: item on_loan, will be checked-in normally.
            loan = self.get_first_loan_by_state(state=LoanState.ITEM_ON_LOAN)
        return loan, kwargs

    def complete_action_missing_params(
            self, item=None, checkin_loan=None, **kwargs):
        """Add the missing parameters before executing a circulation action."""
        # TODO: find a better way to code this part.
        if not checkin_loan:
            loan = None
            loan_pid = kwargs.get('pid')
            if loan_pid:
                loan = Loan.get_record_by_pid(loan_pid)
            patron_pid = kwargs.get('patron_pid')
            if patron_pid and not loan:
                data = {
                    'item_pid': item_pid_to_object(item.pid),
                    'patron_pid': patron_pid
                }
                data.setdefault(
                    'transaction_date', datetime.utcnow().isoformat())
                loan = Loan.create(data, dbcommit=True, reindex=True)
            if not patron_pid and loan:
                kwargs.setdefault('patron_pid', loan.patron_pid)

            kwargs.setdefault('pid', loan.pid)
            kwargs.setdefault('patron_pid', patron_pid)
        else:
            kwargs['patron_pid'] = checkin_loan.get('patron_pid')
            kwargs['pid'] = checkin_loan.pid
            loan = checkin_loan

        kwargs['item_pid'] = item_pid_to_object(item.pid)

        kwargs['transaction_date'] = datetime.utcnow().isoformat()
        document_pid = extracted_data_from_ref(item.get('document'))
        kwargs.setdefault('document_pid', document_pid)
        # set the transaction location for the circulation transaction
        transaction_location_pid = kwargs.get(
            'transaction_location_pid', None)
        if not transaction_location_pid:
            transaction_library_pid = kwargs.pop(
                'transaction_library_pid', None)
            if transaction_library_pid is not None:
                lib = Library.get_record_by_pid(transaction_library_pid)
                kwargs['transaction_location_pid'] = \
                    lib.get_transaction_location_pid()
        # set the pickup_location_pid field if not found for loans that are
        # ready for checkout.
        if not kwargs.get('pickup_location_pid') and \
           loan.get('state') in [LoanState.CREATED, LoanState.ITEM_AT_DESK]:
            kwargs['pickup_location_pid'] = \
                kwargs.get('transaction_location_pid')
        return loan, kwargs

    def checkin_item_on_shelf(self, loans_list, **kwargs):
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
            if self.status != ItemStatus.ON_SHELF:
                self.status_update(
                    self, dbcommit=True, reindex=True, forceindex=True)
                raise NoCirculationAction(_(
                    'No circulation action performed: '
                    'Item returned at owning library'))
            raise NoCirculationAction(
                _('No circulation action performed: on shelf'))
        else:
            # CHECKIN_1_1_2: item library != transaction library
            # item will be checked-in in an external library, no
            # circulation action performed, add item status in_transit
            self['status'] = ItemStatus.IN_TRANSIT
            self.status_update(
                self, on_shelf=False, dbcommit=True, reindex=True,
                forceindex=True)
            raise NoCirculationAction(
                _('No circulation action performed: in transit added'))

    def checkin_item_at_desk(self, **kwargs):
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
                _('No circulation action performed: item at desk'))

        # CHECKIN_2_2: pickup location != transaction library
        # item is: in_transit
        at_desk_loan['state'] = LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
        at_desk_loan.update(at_desk_loan, dbcommit=True, reindex=True)
        self['status'] = ItemStatus.IN_TRANSIT
        self.status_update(
            self, on_shelf=False, dbcommit=True, reindex=True, forceindex=True)
        raise NoCirculationAction(
            _('No circulation action performed: in transit added'))

    def checkin_item_in_transit_for_pickup(self, **kwargs):
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
                _('No circulation action performed: in transit for pickup'))

    def checkin_item_in_transit_to_house(self, loans_list, **kwargs):
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
            if not transaction_item_libraries:
                # CHECKIN_5_1_2: item location != transaction library
                # (no action, item is: in_transit (IN_TRANSIT_TO_HOUSE))
                raise NoCirculationAction(
                    _('No circulation action performed: in transit to house'))
            # CHECKIN_5_1_1: item location = transaction library
            # (house_receive current loan, item is: on_shelf)
            kwargs['receive_in_transit_request'] = True
            loan = in_transit_loan
        else:
            # CHECKIN_5_2: item has pending requests.
            loan, kwargs = self.checkin_item_in_transit_to_house_with_requests(
                in_transit_loan, **kwargs)
        return loan, kwargs

    def checkin_item_in_transit_to_house_with_requests(
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
                    # item library (no action, item is: IN_TRANSIT)
                    raise NoCirculationAction(
                        _('No circulation action performed: in transit'))
                else:
                    # CHECKIN_5_2_2_2: pickup location of first PENDING loan !=
                    # item library (checkin current loan, item is: in_transit)
                    # [automatic cancel current, automatic validate first loan]
                    kwargs['cancel_current_and_receive_first'] = True
                    loan = in_transit_loan
        return loan, kwargs

    def validate_item_first_pending_request(self, **kwargs):
        """Validate the first pending request for an item.

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

    def compare_item_pickup_transaction_libraries(self, **kwargs):
        """Compare item library, pickup and transaction libraries.

        :param kwargs : all others named arguments
        :return a dict comparison with the following boolean keys
            `transaction_item_libraries`: between transaction and item
            `transaction_pickup_libraries`: between transaction and pickup
            `item_pickup_libraries`: between item and pickup
        """
        trans_loc_pid = kwargs.pop('transaction_location_pid', None)
        trans_lib_pid = kwargs.pop('transaction_library_pid', None)
        if not trans_lib_pid:
            trans_lib_pid = Location.get_record_by_pid(trans_loc_pid)\
                .library_pid

        pickup_loc_pid = kwargs.pop('pickup_location_pid', None)
        pickup_lib_pid = kwargs.pop('pickup_library_pid', None)
        if not pickup_lib_pid:
            if not pickup_loc_pid:
                pickup_lib_pid = trans_lib_pid
            else:
                pickup_lib_pid = Location\
                    .get_record_by_pid(pickup_loc_pid)\
                    .library_pid

        return {
            'transaction_item_libraries': self.library_pid == trans_lib_pid,
            'transaction_pickup_libraries': pickup_lib_pid == trans_lib_pid,
            'item_pickup_libraries': self.library_pid == pickup_lib_pid
        }

    @check_operation_allowed(ItemCirculationAction.CHECKOUT)
    @add_action_parameters_and_flush_indexes
    def checkout(self, current_loan, **kwargs):
        """Checkout item to the user."""
        action_params, actions = self.prior_checkout_actions(kwargs)
        loan = Loan.get_record_by_pid(action_params.get('pid'))
        current_loan = loan or Loan.create(
            action_params,
            dbcommit=True,
            reindex=True
        )
        old_state = current_loan.get('state')

        # If 'end_date' is specified, we need to check if the selected date is
        # not a closed date. If it's a closed date, then we need to update the
        # value to the next open day.
        if 'end_date' in action_params:
            # circulation parameters are to calculate from transaction library.
            transaction_library_pid = LocationsSearch().get_record_by_pid(
                kwargs.get('transaction_location_pid')).library.pid
            if not transaction_library_pid:
                transaction_library_pid = self.library_pid
            library = Library.get_record_by_pid(transaction_library_pid)
            if not library.is_open(action_params['end_date'], True):
                # If library has no open dates, keep the default due date
                # to avoid circulation errors
                with suppress(LibraryNeverOpen):
                    new_end_date = library.next_open(action_params['end_date'])
                    new_end_date = new_end_date.astimezone()\
                        .replace(microsecond=0).isoformat()
                    action_params['end_date'] = new_end_date
        # Call invenio_circulation for 'checkout' trigger
        loan = current_circulation.circulation.trigger(
            current_loan,
            **dict(action_params, trigger='checkout')
        )
        new_state = loan.get('state')
        if old_state == new_state:
            current_app.logger.error(
                f'Loan state has not changed after CHECKOUT: {loan.pid} '
                f'state: {old_state} '
                f'kwargs: {kwargs}'
            )
        actions.update({LoanAction.CHECKOUT: loan})
        return self, actions

    @add_action_parameters_and_flush_indexes
    def cancel_loan(self, current_loan, **kwargs):
        """Cancel a given item loan for a patron."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='cancel')
        )
        return self, {
            LoanAction.CANCEL: loan
        }

    def cancel_item_request(self, pid, **kwargs):
        """A smart cancel request for an item. Some actions are performed.

        during the cancelling process and according to the loan state.
        :param pid: the loan pid for the request to cancel.
        :return: the item record and list of actions performed.
        """
        actions = {}
        loan = Loan.get_record_by_pid(pid)
        # decide  which actions need to be executed according to loan state.
        actions_to_execute = self.checks_before_a_cancel_item_request(
            loan, **kwargs)
        # execute the actions
        if actions_to_execute.get('cancel_loan'):
            item, actions = self.cancel_loan(pid=loan.pid, **kwargs)
        if actions_to_execute.get('loan_update', {}).get('state'):
            loan['state'] = actions_to_execute['loan_update']['state']
            loan.update(loan, dbcommit=True, reindex=True)
            self.status_update(
                self, dbcommit=True, reindex=True, forceindex=True)
            actions.update({LoanAction.UPDATE: loan})
        elif actions_to_execute.get('validate_first_pending'):
            pending = self.get_first_loan_by_state(state=LoanState.PENDING)
            loan_pickup = loan.get('pickup_location_pid', None)
            pending_pickup = pending.get('pickup_location_pid', None)
            # If the item is at_desk at the same location as the next loan
            # pickup we can validate the next loan so that it becomes at desk
            # for the next patron.
            if loan.get('state') == LoanState.ITEM_AT_DESK\
                    and loan_pickup == pending_pickup:
                item, actions = self.cancel_loan(pid=loan.pid, **kwargs)
                kwargs['transaction_location_pid'] = loan_pickup
                kwargs.pop('transaction_library_pid', None)
                item, validate_actions = self.validate_request(
                    pid=pending.pid,
                    **kwargs)
                actions.update(validate_actions)
            # Otherwise, we simply change the state of the next loan and it
            # will be validated at the next checkin at the pickup location.
            else:
                pending['state'] = LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
                pending.update(pending, dbcommit=True, reindex=True)
                item, actions = self.cancel_loan(pid=loan.pid, **kwargs)
                self.status_update(self, dbcommit=True,
                                   reindex=True, forceindex=True)
                actions.update({LoanAction.UPDATE: loan})
        item = self
        return item, actions

    def checks_before_a_cancel_item_request(self, loan, **kwargs):
        """Actions tobe executed before a cancel item request.

        :param loan : the current loan to cancel
        :param kwargs : all others named arguments
        :return: the item record and list of actions performed
        """
        actions_to_execute = {
            'cancel_loan': False,
            'loan_update': {},
            'validate_first_pending': False
        }
        libraries = self.compare_item_pickup_transaction_libraries(**kwargs)
        # List all loan states attached to this item except the loan to cancel.
        # If the list is empty, no pending request/loan are linked to this item
        states = self.get_loans_states_by_item_pid_exclude_loan_pid(
            self.pid, loan.pid)
        if not states:
            if loan['state'] in \
                    [LoanState.PENDING, LoanState.ITEM_IN_TRANSIT_TO_HOUSE]:
                # CANCEL_REQUEST_1_2, CANCEL_REQUEST_5_1_1:
                # cancel the current loan is the only action
                actions_to_execute['cancel_loan'] = True
            elif loan['state'] == LoanState.ITEM_ON_LOAN:
                # CANCEL_REQUEST_3_1: no cancel action is possible on the loan
                # of a CHECKED_IN item.
                raise NoCirculationAction(
                    _('No circulation action is possible: CHECKED_IN'))
            elif loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                # CANCEL_REQUEST_4_1_1: cancelling a ITEM_IN_TRANSIT_FOR_PICKUP
                # loan with no pending request puts the item on in_transit
                # and the loan becomes ITEM_IN_TRANSIT_TO_HOUSE.
                actions_to_execute['loan_update']['state'] = \
                    LoanState.ITEM_IN_TRANSIT_TO_HOUSE
                # Mark the loan to be cancelled to create an
                # OperationLog about this cancellation.
                actions_to_execute['cancel_loan'] = True
            elif loan['state'] == LoanState.ITEM_AT_DESK:
                if not libraries['item_pickup_libraries']:
                    # CANCEL_REQUEST_2_1_1_1: when item library and pickup
                    # pickup library arent equal, update loan to go in_transit.
                    actions_to_execute['loan_update']['state'] = \
                        LoanState.ITEM_IN_TRANSIT_TO_HOUSE
                # Always mark the loan to be cancelled to create an
                # OperationLog about this cancellation.
                actions_to_execute['cancel_loan'] = True
        elif loan['state'] == LoanState.ITEM_AT_DESK and \
                LoanState.PENDING in states:
            # CANCEL_REQUEST_2_1_2: when item at desk with pending loan, cancel
            # the loan triggers an automatic validation of first pending loan.
            actions_to_execute['validate_first_pending'] = True
        elif loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP and \
                LoanState.PENDING in states:
            # CANCEL_REQUEST_4_1_2: when item in_transit with pending loan,
            # cancel the loan triggers an automatic validation of 1st loan.
            actions_to_execute['validate_first_pending'] = True
        elif loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE and \
                LoanState.PENDING in states:
            # CANCEL_REQUEST_5_1_2: when item in_transit with pending loan,
            # cancelling the loan triggers an automatic validation of first
            # pending loan.
            actions_to_execute['validate_first_pending'] = True
        elif loan['state'] == LoanState.PENDING and \
            any(state in states for state in [
                LoanState.ITEM_AT_DESK,
                LoanState.ITEM_ON_LOAN,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
                LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
                LoanState.PENDING]):
            # CANCEL_REQUEST_1_2, CANCEL_REQUEST_2_2, CANCEL_REQUEST_3_2,
            # CANCEL_REQUEST_4_2 CANCEL_REQUEST_5_2:
            # canceling a pending loan does not affect the other active loans.
            actions_to_execute['cancel_loan'] = True

        return actions_to_execute

    @add_action_parameters_and_flush_indexes
    def validate_request(self, current_loan, **kwargs):
        """Validate item request."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='validate_request')
        )
        return self, {
            LoanAction.VALIDATE: loan
        }

    @add_action_parameters_and_flush_indexes
    @check_operation_allowed(ItemCirculationAction.EXTEND)
    def extend_loan(self, current_loan, **kwargs):
        """Extend checkout duration for this item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='extend')
        )
        return self, {
            LoanAction.EXTEND: loan
        }

    @check_operation_allowed(ItemCirculationAction.REQUEST)
    @add_action_parameters_and_flush_indexes
    def request(self, current_loan, **kwargs):
        """Request item for the user and create notifications."""
        old_state = current_loan.get('state')
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='request')
        )
        new_state = loan.get('state')
        if old_state == new_state:
            current_app.logger.error(
                f'Loan state has not changed after REQUEST: {loan.pid} '
                f'state: {old_state} '
                f'kwargs: {kwargs}'
            )
        return self, {
            LoanAction.REQUEST: loan
        }

    @add_action_parameters_and_flush_indexes
    def receive(self, current_loan, **kwargs):
        """Receive an item."""
        loan = current_circulation.circulation.trigger(
            current_loan, **dict(kwargs, trigger='receive')
        )
        return self, {
            LoanAction.RECEIVE: loan
        }

    def checkin_triggers_validate_current_loan(self, actions, **kwargs):
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
            if validate_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP:
                trans_loc = Location.get_record_by_pid(transaction_loc_pid)
                req_loc = Location.get_record_by_pid(
                    request.get('pickup_location_pid'))
                if req_loc.library_pid == trans_loc.library_pid:
                    item, receive_action = self.receive(**request)
                    actions.update(receive_action)
            return item, actions
        return self, actions

    def checkin_triggers_receive_in_transit_current_loan(
            self, actions, **kwargs):
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

    def checkin_triggers_receive_and_validate_requests(
            self, actions, **kwargs):
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

    def checkin_triggers_cancel_and_receive_first_loan(
            self, current_loan, actions, **kwargs):
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

    @add_action_parameters_and_flush_indexes
    def checkin(self, current_loan, **kwargs):
        """Perform a smart checkin action."""
        actions = {}
        # checkin actions for an item on_shelf
        item, actions = self.checkin_triggers_validate_current_loan(
            actions, **kwargs)
        if actions:
            return item, actions
        # checkin actions for an item in_transit with no requests
        item, actions = self.checkin_triggers_receive_in_transit_current_loan(
            actions, **kwargs)
        if actions:
            return item, actions
        # checkin actions for an item in_transit_to_house at home library
        item, actions = self.checkin_triggers_receive_and_validate_requests(
            actions, **kwargs)
        if actions:
            return item, actions
        # checkin actions for an item in_transit_to_house at external library
        item, actions = self.checkin_triggers_cancel_and_receive_first_loan(
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
            if loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP and\
               loan.get('patron_pid') == action_params.get('patron_pid'):
                item, receive_actions = self.receive(**action_params)
                actions.update(receive_actions)
            elif loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE:
                # do not pass the patron_pid when cancelling a loan
                cancel_params = deepcopy(action_params)
                cancel_params.pop('patron_pid')
                item, cancel_actions = self.cancel_loan(**cancel_params)
                actions.update(cancel_actions)
                del action_params['pid']
                # TODO: Check what's wrong in this case because Loan is cancel
                # but loan variable is not updated and after prior_checkout
                # a checkout is done on the item (it becomes ON_LOAN)
        else:
            loan = get_loan_for_item(item_pid_to_object(self.pid))
            if loan and loan['state'] != LoanState.ITEM_AT_DESK:
                item, cancel_actions = self.cancel_loan(pid=loan.get('pid'))
                actions.update(cancel_actions)
        # CHECKOUT_1_2_2: checkout denied if some pending loan are linked to it
        # with different patrons
        # Except while coming from an ITEM_IN_TRANSIT_TO_HOUSE loan because
        # the loan is cancelled and then came up in ON_SHELF to be checkout
        # by the second patron.
        if self.status == ItemStatus.ON_SHELF and \
           loan['state'] != LoanState.ITEM_IN_TRANSIT_TO_HOUSE:
            for res in self.get_item_loans_by_state(state=LoanState.PENDING):
                if res.patron_pid != loan.get('patron_pid'):
                    item_pid = item_pid_to_object(self.pid)
                    msg = "A pending loan exists for patron %s" % \
                        res.patron_pid
                    raise ItemNotAvailableError(
                        item_pid=item_pid, description=msg)
                # exit from loop after evaluation of the first request.
                break
        return action_params, actions

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
        exclude_states = [
            LoanState.ITEM_RETURNED, LoanState.CANCELLED, LoanState.CREATED]
        item_pid_object = item_pid_to_object(item_pid)
        results = current_circulation.loan_search_cls()\
            .filter('term', item_pid__value=item_pid_object['value'])\
            .filter('term', item_pid__type=item_pid_object['type'])\
            .exclude('terms', state=exclude_states)\
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
    def get_pendings_loans(cls, library_pid=None, sort_by='_created'):
        """Return list of sorted pending loans for a given library.

        default sort is set to _created
        """
        # check if library exists
        lib = Library.get_record_by_pid(library_pid)
        if not lib:
            raise Exception('Invalid Library PID')
        # the '-' prefix means a desc order.
        sort_by = sort_by or '_created'
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
    def get_checked_out_loan_infos(cls, patron_pid, sort_by='_created'):
        """Returns sorted checked out loans for a given patron."""
        # the '-' prefix means a desc order.
        sort_by = sort_by or '_created'
        order_by = 'asc'
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            order_by = 'desc'

        results = search_by_patron_item_or_document(
            patron_pid=patron_pid,
            filter_states=[LoanState.ITEM_ON_LOAN]
        ).params(preserve_order=True)\
         .sort({sort_by: {"order": order_by}})\
         .source(['pid', 'item_pid.value'])\
         .scan()
        for data in results:
            yield data.pid, data.item_pid.value

    def get_last_location(self):
        """Returns the location record of the transaction location.

        of the last loan.
        """
        return Location.get_record_by_pid(self.last_location_pid)

    @property
    def last_location_pid(self):
        """Returns the location pid of the circulation transaction location.

        of the last loan.
        """
        loan_location_pid = get_last_transaction_loc_for_item(self.pid)
        if loan_location_pid and Location.get_record_by_pid(loan_location_pid):
            return loan_location_pid
        return self.location_pid

    def patron_has_an_active_loan_on_item(self, patron):
        """Return True if patron has an active loan on the item.

        The new circ specs do allow requests on ITEM_IN_TRANSIT_TO_HOUSE loans.

        :param patron_barcode: the patron barcode.
        :return: True is requested otherwise False.
        """
        if patron:
            search = search_by_patron_item_or_document(
                item_pid=item_pid_to_object(self.pid),
                patron_pid=patron.pid,
                filter_states=[
                    LoanState.PENDING,
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
                    LoanState.ITEM_AT_DESK,
                    LoanState.ITEM_ON_LOAN
                ]).params(preserve_order=True).source(['state'])
            return len(
                list(
                    dict.fromkeys(
                        [result.state for result in search.scan()]))) > 0

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
            reasons.append(_('Item status disallows the operation.'))
        if 'patron' in kwargs:
            patron = kwargs['patron']
            if patron.organisation_pid != item.organisation_pid:
                reasons.append(_('Item and patron are not in the same '
                               'organisation.'))
            if patron.patron.get('barcode') and \
               item.patron_has_an_active_loan_on_item(
                   patron):
                reasons.append(_('Item is already checked-out or requested by '
                               'patron.'))
        return len(reasons) == 0, reasons

    def action_filter(self, action, organisation_pid, library_pid, loan,
                      patron_pid, patron_type_pid):
        """Filter actions."""
        circ_policy = CircPolicy.provide_circ_policy(
            organisation_pid,
            library_pid,
            patron_type_pid,
            self.item_type_circulation_category_pid
        )
        data = {
            'action_validated': True,
            'new_action': None
        }
        if action == 'extend':
            can, reasons = self.can(ItemCirculationAction.EXTEND, loan=loan)
            if not can:
                data['action_validated'] = False
        if action == 'checkout' and not circ_policy.can_checkout:
            data['action_validated'] = False
        elif (
            action == 'receive' and circ_policy.can_checkout and
            loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP and
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
            organisation_pid = self.organisation_pid
            library_pid = self.library_pid
            patron_pid = loan.get('patron_pid')
            patron_type_pid = Patron.get_record_by_pid(
                patron_pid).patron_type_pid
            for transition in transitions.get(loan['state']):
                action = transition.get('trigger')
                data = self.action_filter(
                    action=action,
                    organisation_pid=organisation_pid,
                    library_pid=library_pid,
                    loan=loan,
                    patron_pid=patron_pid,
                    patron_type_pid=patron_type_pid
                )

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

    @classmethod
    def status_update(cls, item, on_shelf=True, dbcommit=False,
                      reindex=False, forceindex=False):
        """Update item status.

        The item normally inherits its status from its active loan. In other
        cases it goes back to on_shelf

        :param item: the item record
        :param on_shelf: A boolean to indicate that item is candidate to go
                         on_shelf
        :param dbcommit: commit record to database
        :param reindex: reindex record
        :param forceindex: force the reindexation
        """
        loan = get_loan_for_item(item_pid_to_object(item.pid))
        if loan:
            item['status'] = cls.statuses[loan['state']]
        elif item['status'] != ItemStatus.MISSING and on_shelf:
            item['status'] = ItemStatus.ON_SHELF
        item.commit()
        if dbcommit:
            item.dbcommit(reindex=True, forceindex=True)

    def item_has_active_loan_or_request(self):
        """Return True if active loan or a request found for item."""
        states = [LoanState.PENDING] + \
            current_app.config['CIRCULATION_STATES_LOAN_ACTIVE']
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid),
            filter_states=states,
        )
        return bool(search.count())

    def return_missing(self):
        """Return the missing item.

        The item's status will be set to ItemStatus.ON_SHELF.
        """
        # TODO: check transaction location
        self['status'] = ItemStatus.ON_SHELF
        self.status_update(
            self, dbcommit=True, reindex=True, forceindex=True)
        return self, {
            LoanAction.RETURN_MISSING: None
        }

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        # avoid circular import
        from rero_ils.modules.collections.api import CollectionsSearch
        from rero_ils.modules.local_fields.api import LocalFieldsSearch

        query_loans = search_by_pid(
            item_pid=item_pid_to_object(self.pid),
            exclude_states=[
                LoanState.CREATED,
                LoanState.CANCELLED,
                LoanState.ITEM_RETURNED,
            ]
        )
        query_fees = PatronTransactionsSearch()\
            .filter('term', item__pid=self.pid)\
            .filter('term', status='open')\
            .filter('range', total_amount={'gt': 0})
        query_collections = CollectionsSearch()\
            .filter('term', items__pid=self.pid)
        query_local_fields = LocalFieldsSearch()\
            .get_local_fields(self.provider.pid_type, self.pid)

        if get_pids:
            loans = sorted_pids(query_loans)
            fees = sorted_pids(query_fees)
            collections = sorted_pids(query_collections)
            local_fields = sorted_pids(query_local_fields)
        else:
            loans = query_loans.count()
            fees = query_fees.count()
            collections = query_collections.count()
            local_fields = query_local_fields.count()
        links = {
            'loans': loans,
            'fees': fees,
            'collections': collections,
            'local_fields': local_fields
        }
        return {k: v for k, v in links.items() if v}

    def get_requests(self, sort_by=None, output=None):
        """Return sorted pending, item_on_transit, item_at_desk loans.

        :param sort_by: the sort to result. default sort is _created.
        :param output: the type of output. 'pids', 'count' or 'obj' (default)
        :return depending of output parameter:
            - 'obj': a generator ``Loan`` objects.
            - 'count': the request counter.
            - 'pids': the request pids list
        """

        def _list_obj():
            order_by = 'asc'
            sort_term = sort_by or '_created'
            if sort_term.startswith('-'):
                (sort_term, order_by) = (sort_term[1:], 'desc')
            es_query = query\
                .params(preserve_order=True)\
                .sort({sort_term: {'order': order_by}})
            for result in es_query.scan():
                yield Loan.get_record_by_pid(result.pid)

        query = search_by_pid(
            item_pid=item_pid_to_object(self.pid), filter_states=[
                LoanState.PENDING,
                LoanState.ITEM_AT_DESK,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
            ]).source(['pid'])
        if output == 'pids':
            return [hit.pid for hit in query.scan()]
        elif output == 'count':
            return query.count()
        else:
            return _list_obj()

    def get_first_loan_by_state(self, state=None):
        """Return the first loan with the given state and attached to item.

        :param state : the loan state
        :return: first loan found otherwise None
        """
        try:
            return next(self.get_item_loans_by_state(state=state))
        except StopIteration:
            return None

    def get_item_loans_by_state(self, state=None, sort_by=None):
        """Return sorted item loans with a given state.

        default sort is _created.
        :param state : the loan state
        :param sort_by : field to use for sorting
        :return: loans found
        """
        search = search_by_pid(
            item_pid=item_pid_to_object(self.pid), filter_states=[
                state
            ]).params(preserve_order=True).source(['pid'])
        order_by = 'asc'
        sort_by = sort_by or '_created'
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

    def is_available(self):
        """Get availability for item.

        Note: if the logic has to be changed here please check also for
        documents and holdings availability.
        """
        from ..api import ItemsSearch

        items_query = ItemsSearch().available_query()

        # check item availability
        if not items_query.filter('term', pid=self.pid).count():
            return False

        # --------------- Loans -------------------
        # unavailable if the current item has active loans
        return not self.item_has_active_loan_or_request()

    @property
    def availability_text(self):
        """Availability text to display for an item."""
        circ_category = self.circulation_category
        if circ_category.get('negative_availability'):
            return circ_category.get('displayed_status', []) + [{
                'language': 'default',
                'label': circ_category.get('name')
            }]
        label = self.status
        if self.is_issue and self.issue_status != ItemIssueStatus.RECEIVED:
            label = self.issue_status
        return [{
            'language': 'default',
            'label': label
        }]

    @property
    def temp_item_type_negative_availability(self):
        """Get the temporary item type neg availability."""
        if self.get('temporary_item_type'):
            return ItemType.get_record_by_pid(extracted_data_from_ref(
                self.get('temporary_item_type'))
            ).get('negative_availability', False)
        return False

    def get_item_end_date(self, format='short', time_format='medium',
                          language=None):
        """Get item due date for a given item.

        :param format: The date format, ex: 'full', 'medium', 'short'
                        or custom
        :param time_format: The time format, ex: 'medium', 'short' or custom
        :param language: The language to fix the language format
        :return: original date, formatted date or None
        """
        loan = get_loan_for_item(item_pid_to_object(self.pid))
        if loan:
            end_date = loan['end_date']
            if format:
                return format_date_filter(
                    end_date,
                    date_format=format,
                    time_format=time_format,
                    locale=language,
                )
            return end_date
        return None

    def get_extension_count(self):
        """Get item renewal count."""
        loan = get_loan_for_item(item_pid_to_object(self.pid))
        if loan:
            return loan.get('extension_count', 0)
        return 0

    def number_of_requests(self):
        """Get number of requests for a given item."""
        return self.get_requests(output='count')

    def patron_request_rank(self, patron):
        """Get the rank of patron in list of requests on this item."""
        if patron:
            requests = self.get_requests()
            for rank, request in enumerate(requests, start=1):
                if request['patron_pid'] == patron.pid:
                    return rank
        return 0

    def is_requested_by_patron(self, patron_barcode):
        """Check if the item is requested by a given patron."""
        patron = Patron.get_patron_by_barcode(
            barcode=patron_barcode, org_pid=self.organisation_pid)
        if patron:
            request = get_request_by_item_pid_by_patron_pid(
                item_pid=self.pid, patron_pid=patron.pid
            )
            if request:
                return True
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
        from .api import Item
        loan_infos = cls.get_checked_out_loan_infos(
            patron_pid=patron_pid,
            sort_by=sort_by
        )
        returned_item_pids = []
        for loan_pid, item_pid in loan_infos:
            if item_pid not in returned_item_pids:
                returned_item_pids.append(item_pid)
                yield Item.get_record_by_pid(item_pid)
