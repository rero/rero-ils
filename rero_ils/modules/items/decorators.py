# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Decorators about items."""

from functools import wraps

from flask import current_app
from invenio_circulation.errors import CirculationException
from invenio_records_rest.utils import obj_or_import_string

from rero_ils.modules.loans.api import Loan, \
    get_request_by_item_pid_by_patron_pid


def add_action_parameters_and_flush_indexes(function):
    """Add missing action and validate parameters.

    For each circulation action, this method ensures that all required
    parameters are given. Adds missing parameters if any. Ensures the right
    loan transition for the given action.
    """
    @wraps(function)
    def wrapper(item, *args, **kwargs):
        """Executed before loan action."""
        checkin_loan = None
        if function.__name__ == 'validate_request':
            # checks if the given loan pid can be validated
            item.prior_validate_actions(**kwargs)
        elif function.__name__ == 'checkin':
            # the smart checkin requires extra checks/actions before a checkin
            loan, kwargs = item.prior_checkin_actions(**kwargs)
            checkin_loan = loan
        # CHECKOUT: Case where no loan PID
        elif function.__name__ == 'checkout' and not kwargs.get('pid'):
            patron_pid = kwargs['patron_pid']
            item_pid = item.pid
            request = get_request_by_item_pid_by_patron_pid(
                item_pid=item_pid, patron_pid=patron_pid)
            if request:
                kwargs['pid'] = request.pid
        elif function.__name__ == 'extend_loan':
            loan, kwargs = item.prior_extend_loan_actions(**kwargs)
            checkin_loan = loan

        loan, kwargs = item.complete_action_missing_params(
                item=item, checkin_loan=checkin_loan, **kwargs)
        Loan.check_required_params(function.__name__, **kwargs)
        item, action_applied = function(item, loan, *args, **kwargs)
        item.change_status_commit_and_reindex()
        return item, action_applied
    return wrapper


def check_operation_allowed(action):
    """Check if a specific action is allowed on an item.

    Check if an 'override_blocking' parameter is present. If this param is
    present and set to True (or corresponding True values [1, 'true', ...])
    then no CIRCULATION_ACTIONS_VALIDATION should be tested.
    Remove this parameter from the data arguments.

    Check the CIRCULATION_ACTIONS_VALIDATION configuration file and execute
    function corresponding to the action specified. All function are execute
    until one return False (action denied) or all actions are successful.

    :param action: the action to check as ItemCirculationAction part.
    :raise CirculationException if a function disallow the operation.
    """
    def inner_function(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            override_blocking = kwargs.pop('override_blocking', False)
            override_blocking = bool(override_blocking)
            if not override_blocking:
                actions = current_app.config.get(
                    'CIRCULATION_ACTIONS_VALIDATION', {})
                for func_name in actions.get(action, []):
                    func_callback = obj_or_import_string(func_name)
                    can, reasons = func_callback(args[0], **kwargs)
                    if not can:
                        raise CirculationException(description=reasons[0])
            return func(*args, **kwargs)
        return decorated_view
    return inner_function
