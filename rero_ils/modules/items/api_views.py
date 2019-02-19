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
from ..loans.api import Loan
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
    """."""
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
    """."""
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
        except CirculationException:
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
    items_loans = Item.get_checked_out_items(patron_pid)
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


@api_blueprint.route('/barcode/<item_barcode>', methods=['GET'])
@check_authentication
@jsonify_error
def item(item_barcode):
    """HTTP GET request for requested loans for a library."""
    item = Item.get_item_by_barcode(item_barcode)
    if not item:
        abort(404)
    loan = get_loan_for_item(item.pid)
    if loan:
        loan = Loan.get_record_by_pid(loan['loan_pid']).dumps_for_circulation()
    return jsonify({
        'metadata': {
            'item': item.dumps_for_circulation(),
            'loan': loan
        }
    })
