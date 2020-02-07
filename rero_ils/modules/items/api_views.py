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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, abort, current_app, jsonify
from flask import request as flask_request
from flask_login import current_user
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.errors import CirculationException
from werkzeug.exceptions import NotFound

from .api import Item, ItemStatus
from ..circ_policies.api import CircPolicy
from ..libraries.api import Library
from ..loans.api import Loan
from ..loans.utils import can_be_requested
from ..patrons.api import Patron
from ...permissions import librarian_permission

api_blueprint = Blueprint(
    'api_item',
    __name__,
    url_prefix='/item'
)


def check_authentication(func):
    """Decorator to check authentication for items HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not librarian_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)

    return decorated_view


def jsonify_error(func):
    """Jsonify errors."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotFound as error:
            raise(error)
        except Exception as error:
            # raise(error)
            current_app.logger.error(str(error))
            return jsonify({'status': 'error: {error}'.format(
                error=error)}), 500
    return decorated_view


def jsonify_action(func):
    """Jsonify loan actions."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            data = flask_request.get_json()
            item_pid = data.get('item_pid')
            if item_pid:
                item = Item.get_record_by_pid(item_pid)
            else:
                item_barcode = data.pop('item_barcode', None)
                item = Item.get_item_by_barcode(item_barcode)
            if not item:
                abort(404)
            trans_lib_pid = data.pop('transaction_library_pid', None)
            if trans_lib_pid is not None:
                lib = Library.get_record_by_pid(trans_lib_pid)
                data['transaction_location_pid'] = \
                    lib.get_pickup_location_pid()
            item_data, action_applied = \
                func(item, data, *args, **kwargs)

            for action, loan in action_applied.items():
                if loan:
                    action_applied[action] = loan.dumps_for_circulation()

            return jsonify({
                'metadata': item_data.dumps_for_circulation(),
                'action_applied': action_applied
            })
        except CirculationException as error:
            abort(403)
        except NotFound as error:
            raise(error)
        except Exception as error:
            # raise(error)
            current_app.logger.error(str(error))
            return jsonify({'status': 'error: {error}'.format(
                error=error)}), 500
    return decorated_view


@api_blueprint.route('/request', methods=['POST'])
@check_authentication
@jsonify_action
def librarian_request(item, data):
    """HTTP GET request for Item request action...

    required_parameters: item_pid_value, location
    """
    return item.request(**data)


@api_blueprint.route('/checkout', methods=['POST'])
@check_authentication
@jsonify_action
def checkout(item, data):
    """HTTP request for Item checkout action.

    required_parameters: patron_pid, item_pid
    """
    return item.checkout(**data)


@api_blueprint.route("/checkin", methods=['POST'])
@check_authentication
@jsonify_action
def checkin(item, data):
    """HTTP request for Item return action.

    required_parameters: item_pid
    """
    return item.checkin(**data)


@api_blueprint.route('/automatic_checkin', methods=['POST'])
@check_authentication
@jsonify_action
def automatic_checkin(item, data):
    """HTTP request for Item circulation actions.

    required_parameters: item_barcode
    """
    trans_loc_pid = data.get('transaction_location_pid')
    return item.automatic_checkin(trans_loc_pid)


@api_blueprint.route("/cancel", methods=['POST'])
@check_authentication
@jsonify_action
def cancel_loan(item, params):
    """HTTP request for cancel action."""
    return item.cancel_loan(**params)


@api_blueprint.route("/lose", methods=['POST'])
@check_authentication
@jsonify_action
def lose(item, params):
    """HTTP request for cancel action."""
    return item.lose()


@api_blueprint.route('/validate', methods=['POST'])
@check_authentication
@jsonify_action
def validate_request(item, data):
    """HTTP request for Item request validation action..

    required_parameters: item_pid
    """
    return item.validate_request(**data)


@api_blueprint.route('/receive', methods=['POST'])
@check_authentication
@jsonify_action
def receive(item, data):
    """HTTP HTTP request for receive item action..

    required_parameters: item_pid
    """
    return item.receive(**data)


@api_blueprint.route('/return_missing', methods=['POST'])
@check_authentication
@jsonify_action
def return_missing(item, data=None):
    """HTTP request for Item return_missing action..

    required_parameters: item_pid
    """
    return item.return_missing()


@api_blueprint.route('/extend_loan', methods=['POST'])
@check_authentication
@jsonify_action
def extend_loan(item, data):
    """HTTP request for Item due date extend action..

    required_parameters: item_pid
    """
    return item.extend_loan(**data)


@api_blueprint.route('/requested_loans/<library_pid>', methods=['GET'])
@check_authentication
@jsonify_error
def requested_loans(library_pid):
    """HTTP GET request for sorted requested loans for a library."""
    sort_by = flask_request.args.get('sort')
    items_loans = Item.get_requests_to_validate(
        library_pid=library_pid, sort_by=sort_by)
    metadata = []
    for item, loan in items_loans:
        metadata.append({
            'item': item.dumps_for_circulation(sort_by=sort_by),
            'loan': loan.dumps_for_circulation()
        })
    return jsonify({
        'hits': {
            'total': len(metadata),
            'hits': metadata
        }
    })


@api_blueprint.route('/loans/<patron_pid>', methods=['GET'])
@check_authentication
@jsonify_error
def loans(patron_pid):
    """HTTP GET request for sorted loans for a patron pid."""
    sort_by = flask_request.args.get('sort')
    items_loans = Item.get_checked_out_items(
        patron_pid=patron_pid, sort_by=sort_by)
    metadata = []
    for item, loan in items_loans:
        item_dumps = item.dumps_for_circulation(sort_by=sort_by)
        metadata.append({
            'item': item_dumps,
            'loan': loan.dumps_for_circulation()
        })
    return jsonify({
        'hits': {
            'total': len(metadata),
            'hits': metadata
        }
    })


@api_blueprint.route('/barcode/<item_barcode>', methods=['GET'])
@check_authentication
@jsonify_error
def item(item_barcode):
    """HTTP GET request for requested loans for a library item and patron."""
    item = Item.get_item_by_barcode(item_barcode)
    if not item:
        abort(404)
    loan = get_loan_for_item(item.pid)
    if loan:
        loan = Loan.get_record_by_pid(loan.get('pid')).dumps_for_circulation()
    item_dumps = item.dumps_for_circulation()
    patron_pid = flask_request.args.get('patron_pid')

    if patron_pid:
        patron_type_pid = Patron.get_record_by_pid(
            patron_pid).patron_type_pid

        circ_policy = CircPolicy.provide_circ_policy(
            item.library_pid,
            patron_type_pid,
            item.item_type_pid
        )
        actions = item_dumps.get('actions')
        new_actions = []
        for action in actions:
            if action == 'checkout' and circ_policy.get('allow_checkout'):
                if item.number_of_requests() > 0:
                    patron_barcode = Patron.get_record_by_pid(
                        patron_pid).get('barcode')
                    if item.patron_request_rank(patron_barcode) == 1:
                        new_actions.append(action)
                else:
                    new_actions.append(action)
            if (
                    action == 'receive' and
                    circ_policy.get('allow_checkout') and
                    item.number_of_requests() == 0
            ):
                new_actions.append('checkout')
        item_dumps['actions'] = new_actions
    return jsonify({
        'metadata': {
            'item': item_dumps,
            'loan': loan
        }
    })


@api_blueprint.route('/availabilty/<item_pid>', methods=['GET'])
@check_authentication
@jsonify_error
def item_availability(item_pid):
    """HTTP GET request for item availability."""
    item = Item.get_record_by_pid(item_pid)
    if not item:
        abort(404)
    return jsonify({
        'availability': item.available
    })


@api_blueprint.route(
    '/<item_pid>/can_request/<library_pid>/<patron_barcode>', methods=['GET'])
@check_authentication
@jsonify_error
def can_request(item_pid, library_pid, patron_barcode):
    """HTTP request to check if a librarian can request an item for a patron.

    required_parameters: item_pid, library_pid, patron_barcode
    """
    return is_librarian_can_request_item_for_patron(
        item_pid, library_pid, patron_barcode)


def jsonify_response(response=False, reason=None):
    """Jsonify api response."""
    return jsonify({
        'can_request': response,
        'reason': reason
    })


def is_librarian_can_request_item_for_patron(
        item_pid, library_pid, patron_barcode):
    """Check if a librarian can request an item for a patron.

    required_parameters: item_pid, library_pid, patron_barcode
    """
    item = Item.get_record_by_pid(item_pid)
    if not item:
        return jsonify_response(reason='Item not found.')
    patron = Patron.get_patron_by_barcode(patron_barcode)
    if not patron:
        return jsonify_response(reason='Patron not found.')
    library = Library.get_record_by_pid(library_pid)
    if not library:
        return jsonify_response(reason='Library not found.')
    # Create a loan
    loan = Loan({
        'patron_pid': patron.pid, 'item_pid': item.pid,
        'library_pid': library_pid})
    if not can_be_requested(loan):
        return jsonify_response(
            reason='Circulation policies do not allow request on this item.')
    if item.status != ItemStatus.MISSING:
        loaned_to_patron = item.is_loaned_to_patron(patron_barcode)
        if loaned_to_patron:
            return jsonify_response(
                reason='Item is already checked-out or requested by patron.')
        return jsonify_response(
            response=True, reason='Request is possible.')
    else:
        return jsonify_response(
            reason='Item status does not allow requests.')
