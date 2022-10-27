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

"""Blueprint used for acquuisition account API."""

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify, request

from rero_ils.modules.decorators import check_logged_as_librarian, \
    jsonify_error

from .api import AcqAccount

api_blueprint = Blueprint(
    'api_acq_account',
    __name__,
    url_prefix='/acq_accounts'
)


@api_blueprint.route('/transfer_funds', methods=['GET'])
@check_logged_as_librarian
@jsonify_error
def transfer_funds():
    """HTTP GET request to transfer funds between accounts.

    USAGE : /api/acq_accounts/transfer_funds?source=<from>&target=<until>
            &amount=<amount>

    parameters:
      * source: the source account PID.
      * target: the target account PID.
      * amount: the amount to transfer between both accounts.

    :return HTTP 200: if the transfer is well done
    :return HTTP 400: the transfer can't be done. Check error message to know
                      the reason.
    :return HTTP 401: Unauthorized
    """
    # Get argument values from query string :
    #   * source: source account pid. Account must exists and active.
    #   * target: target account pid. Account must exists and active.
    #   * amount: the amount to transfer. Must be a positive number.
    for arg_name in ['source', 'target', 'amount']:
        if arg_name not in request.args:
            raise KeyError(f"'{arg_name}' argument is required !")
    source_acq = AcqAccount.get_record_by_pid(request.args['source'])
    if source_acq is None:
        raise ValueError('Unable to load source account.')
    elif not source_acq.is_active:
        raise ValueError('Source account isn\'t active.')
    target_acq = AcqAccount.get_record_by_pid(request.args['target'])
    if target_acq is None:
        raise ValueError('Unable to load target account.')
    elif not target_acq.is_active:
        raise ValueError('Target account isn\'t active.')
    amount = float(request.args['amount'])
    if amount < 0:
        raise ValueError("'amount' should be a positive number.")

    # Execute the transfer between source and target account.
    source_acq.transfer_fund(target_acq, amount)
    return jsonify({})
