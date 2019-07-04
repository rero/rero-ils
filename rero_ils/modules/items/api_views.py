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

from flask import Blueprint, abort, jsonify
from flask import request as flask_request
from flask_login import current_user
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.errors import CirculationException
from werkzeug.exceptions import NotFound

from .api import Item
from ..circ_policies.api import CircPolicy
from ..loans.api import Loan
from ..loans.utils import extend_loan_data_is_valid
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
        except NotFound as e:
            raise(e)
        except Exception as e:
            # raise(e)
            return jsonify({'status': 'error: {error}'.format(error=e)}), 500
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
                item_barcode = data.pop('item_barcode')
                item = Item.get_item_by_barcode(item_barcode)
            if not item:
                abort(404)

            item_data, action_applied = func(item, data, *args, **kwargs)

            for action, loan in action_applied.items():
                if loan:
                    action_applied[action] = loan.dumps_for_circulation()

            return jsonify({
                'metadata': item_data.dumps_for_circulation(),
                'action_applied': action_applied
            })
        except CirculationException as e:
            abort(403)
        except NotFound as e:
            raise(e)
        except Exception as e:
            # raise(e)
            return jsonify({'status': 'error: {error}'.format(error=e)}), 500
    return decorated_view


@api_blueprint.route('/request', methods=['POST'])
@check_authentication
@jsonify_action
def librarian_request(item, data):
    """HTTP GET request for Item request action...

    required_parameters: item_pid_value, location
    """
    return item.request(**data)


def prior_checkout_actions(item, data):
    """Actions executed prior to a checkout."""
    if data.get('loan_pid'):
        loan = Loan.get_record_by_pid(data.get('loan_pid'))
        if (
            loan.get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP' and
            loan.get('patron_pid') == data.get('patron_pid')
        ):
            item.receive(**data)
        if loan.get('state') == 'ITEM_IN_TRANSIT_TO_HOUSE':
            item.cancel_loan(loan_pid=loan.get('loan_pid'))
            del data['loan_pid']
    else:
        loan = get_loan_for_item(item.pid)
        if loan:
            item.cancel_loan(loan_pid=loan.get('loan_pid'))
    return data


@api_blueprint.route('/checkout', methods=['POST'])
@check_authentication
@jsonify_action
def checkout(item, data):
    """HTTP request for Item checkout action.

    required_parameters: patron_pid, item_pid
    """
    new_data = prior_checkout_actions(item, data)
    return item.checkout(**new_data)


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
    return item.automatic_checkin()


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
    """HTTP GET request for requested loans for a library."""
    items_loans = Item.get_requests_to_validate(library_pid)
    metadata = []
    for item, loan in items_loans:
        metadata.append({
            'item': item.dumps_for_circulation(),
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
    """HTTP GET request for requested loans for a library."""
    patron_type_pid = Patron.get_record_by_pid(
        patron_pid).patron_type_pid
    items_loans = Item.get_checked_out_items(patron_pid)
    metadata = []
    for item, loan in items_loans:
        item_dumps = item.dumps_for_circulation()
        actions = item_dumps.get('actions')
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
        loan = Loan.get_record_by_pid(loan['loan_pid']).dumps_for_circulation()
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
