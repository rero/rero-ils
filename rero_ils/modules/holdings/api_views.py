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

from flask import Blueprint, abort, jsonify

from .api import Holding
from ..items.api_views import check_authentication, jsonify_error

api_blueprint = Blueprint(
    'api_holding',
    __name__,
    url_prefix='/holding'
)


@api_blueprint.route('/availabilty/<holding_pid>', methods=['GET'])
@check_authentication
@jsonify_error
def holding_availability(holding_pid):
    """HTTP GET request for holding availability."""
    holding = Holding.get_record_by_pid(holding_pid)
    if not holding:
        abort(404)
    return jsonify({
        'availability': holding.available
    })


@api_blueprint.app_template_filter()
def holding_loan_condition(holding_pid):
    """HTTP GET request for holding loan condition."""
    holding = Holding.get_record_by_pid(holding_pid)
    if not holding:
        abort(404)
    return jsonify({
        'loan_condition': holding.get_holding_loan_conditions()
    })
