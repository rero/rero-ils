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

"""Blueprint used for loading templates."""


from __future__ import absolute_import, print_function

from copy import deepcopy
from functools import wraps

from elasticsearch import exceptions
from flask import Blueprint, abort, current_app, jsonify
from flask import request as flask_request
from invenio_circulation.errors import CirculationException, \
    MissingRequiredParameterError
from invenio_db import db
from jinja2.exceptions import TemplateSyntaxError, UndefinedError
from werkzeug.exceptions import NotFound, Unauthorized

from rero_ils.modules.decorators import check_authentication
from rero_ils.modules.documents.views import record_library_pickup_locations
from rero_ils.modules.errors import NoCirculationActionIsPermitted, \
    RegularReceiveNotAllowed
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemIssueStatus, ItemStatus
from rero_ils.modules.items.views.api_views import \
    check_authentication_for_request, check_logged_user_authentication
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import get_ref_for_pid
from rero_ils.permissions import can_receive_regular_issue

from .api import Holding
from .models import HoldingCirculationAction

api_blueprint = Blueprint(
    'api_holding',
    __name__,
    url_prefix='/holding'
)


def jsonify_error(func):
    """Jsonify errors.

    :param func: function that use this decorator
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (Unauthorized, NotFound) as error:
            raise error
        except (TemplateSyntaxError, UndefinedError) as error:
            return jsonify(
                {'status': f'error: {error}'}), 400
        except Exception as error:
            current_app.logger.error(str(error))
            db.session.rollback()
            return jsonify(
                {'status': f'error: {error}'}), 500
    return decorated_view


@api_blueprint.route('/<holding_pid>/patterns/preview', methods=['GET'])
@check_authentication
@jsonify_error
def patterns_preview(holding_pid):
    """HTTP GET request for holdings pattern preview.

    Required parameters: holding_pid
    Optional parameters: size: number of previewed issues - by default 10
    """
    try:
        size = flask_request.args.get('size')
        number_issues = int(size) if size else 10
    except ValueError as error:
        number_issues = 10
    holding = Holding.get_record_by_pid(holding_pid)
    if holding and holding.get('holdings_type') != 'serial':
        return jsonify({'status': 'error: invalid holdings type'}), 400
    issues = holding.prediction_issues_preview(predictions=number_issues)
    return jsonify({'issues': issues})


@api_blueprint.route("/pattern/preview", methods=['POST'])
@check_authentication
@jsonify_error
def pattern_preview():
    """HTTP POST for patterns preview of first n issues for a regular patterns.

    Required parameters: data contains the json of holdings record to preview
    Optional parameters: size: number of previewed issues - by default 10
    """
    patterns_data = flask_request.get_json()
    pattern = patterns_data.get('data', {})
    size = patterns_data.get('size', 10)
    if pattern and pattern.get('frequency') == 'rdafr:1016':
        return jsonify({'status': 'error: irregular frequency'}), 400
    issues = Holding.prediction_issues_preview_for_pattern(
        pattern, number_of_predictions=size)
    return jsonify({'issues': issues})


@api_blueprint.route('/<holding_pid>/issues', methods=['POST'])
@jsonify_error
@check_authentication
def receive_regular_issue(holding_pid):
    """HTTP POST for receiving the next expected issue for a holding.

    For a quick receive, do not pass the item parameter
    For a customized receive, send the item fields in the item parameter.

    Required parameters:
        holding_pid: the pid of the holdings.
    Optional parameters:
        item: the item of type issue to create.
    """
    data = flask_request.get_json()
    holding = Holding.get_record_by_pid(holding_pid)
    if not holding:
        abort(404, "Holding not found")
    # librarian of same holdings library may receive issues
    # system librarians may receive for all libraries of organisation.
    if not can_receive_regular_issue(holding):
        abort(401)
    item = data.get('item', {})
    try:
        issue = holding.create_regular_issue(
            status=ItemIssueStatus.RECEIVED,
            item=item,
            dbcommit=True,
            reindex=True
        )
    except RegularReceiveNotAllowed:
        # receive allowed only on holding of type serials and regular frequency
        abort(400)
    # the created item of type issue is returned
    return jsonify({'issue': issue})


def do_holding_jsonify_action(func):
    """Jsonify loan actions for holdings methods.

    This method for the circulation actions that required access to the holding
    object before executing the invenio-circulation logic.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            data = deepcopy(flask_request.get_json())
            description = data.pop('description')
        except KeyError:
            # The description parameter is missing.
            abort(400, str('missing description parameter.'))

        try:
            holding_pid = data.pop('holding_pid', None)
            holding = Holding.get_record_by_pid(holding_pid)
            if not holding:
                abort(404, 'Holding not found')
            # create a provisional item
            item_metadata = {
                'type': 'provisional',
                'document': {
                    '$ref': get_ref_for_pid('doc', holding.document_pid)},
                'location': {
                    '$ref': get_ref_for_pid('loc', holding.location_pid)},
                'item_type': {'$ref': get_ref_for_pid(
                    'itty', holding.circulation_category_pid)},
                'enumerationAndChronology': description,
                'status': ItemStatus.ON_SHELF,
                'holding': {'$ref': get_ref_for_pid('hold', holding.pid)}
            }
            item = Item.create(item_metadata, dbcommit=True, reindex=True)

            _, action_applied = func(holding, item, data, *args, **kwargs)
            return jsonify({
                'action_applied': action_applied
            })
        except NoCirculationActionIsPermitted as error:
            # The circulation specs do not allow updates on some loan states.
            return jsonify({'status': f'error: {str(error)}'}), 403
        except MissingRequiredParameterError as error:
            # Return error 400 when there is a missing required parameter
            abort(400, str(error))
        except CirculationException as error:
            abort(403, error.description or str(error))
        except NotFound as error:
            raise error
        except exceptions.RequestError as error:
            # missing required parameters
            return jsonify({'status': f'error: {error}'}), 400
        except Exception as error:
            # TODO: need to know what type of exception and document there.
            # raise error
            current_app.logger.error(f'{func.__name__}: {str(error)}')
            return jsonify({'status': f'error: {error}'}), 400
    return decorated_view


@api_blueprint.route('/patron_request', methods=['POST'])
@check_logged_user_authentication
@check_authentication_for_request
@do_holding_jsonify_action
def patron_request(holding, item, data):
    """HTTP POST request for Holding request action by a patron.

    required_parameters:
        holding_pid,
        pickup_location_pid,
        description
    """
    patron_pid = Patron.get_current_patron(holding).pid
    data['patron_pid'] = patron_pid
    data['transaction_user_pid'] = patron_pid
    data['transaction_location_pid'] = data['pickup_location_pid']
    return item.request(**data)


@api_blueprint.route('/request', methods=['POST'])
@check_authentication
@do_holding_jsonify_action
def librarian_request(holding, item, data):
    """HTTP POST request for Holding request action.

    required_parameters:
        holding_pid,
        pickup_location_pid,
        description,
        patron_pid,
        transaction_location_pid or transaction_library_pid,
        transaction_user_pid
    """
    return item.request(**data)


@api_blueprint.route('/<holding_pid>/can_request', methods=['GET'])
@check_logged_user_authentication
@jsonify_error
def can_request(holding_pid):
    """HTTP request to check if an holding can be requested.

    Depending of query string argument, check if either configuration
    allows the request of the holding or if a librarian can request an
    holding for a patron.

    `api/holding/<holding_pid>/can_request` :
         --> only check config
    `api/holding/<holding_pid>/can_request?library_pid=<library_pid>&patron_barcode=<barcode>`:
         --> check if the patron can request an holding (check the cipo)
    """
    kwargs = {}

    holding = Holding.get_record_by_pid(holding_pid)
    if not holding:
        abort(404, 'Holding not found')

    patron_barcode = flask_request.args.get('patron_barcode')
    if patron_barcode:
        kwargs['patron'] = Patron.get_patron_by_barcode(
            barcode=patron_barcode, org_pid=holding.organisation_pid)
        if not kwargs['patron']:
            abort(404, 'Patron not found')

    library_pid = flask_request.args.get('library_pid')
    if library_pid:
        kwargs['library'] = Library.get_record_by_pid(library_pid)
        if not kwargs['library']:
            abort(404, 'Library not found')

    can, reasons = holding.can(HoldingCirculationAction.REQUEST, **kwargs)

    # check the `reasons_not_request` array. If it's empty, the request is
    # allowed, otherwise the request is not allowed and we need to return the
    # reasons why
    response = {'can': can}
    if reasons:
        response['reasons'] = {
            'others': {reason: True for reason in reasons}
        }
    return jsonify(response)


@api_blueprint.route('/<holding_pid>/pickup_locations', methods=['GET'])
@check_logged_user_authentication
@jsonify_error
def get_pickup_locations(holding_pid):
    """HTTP request to return the available pickup locations for an holding.

    :param holding_pid: the holding_pid pid
    """
    holding = Holding.get_record_by_pid(holding_pid)
    if not holding:
        abort(404, 'Holding not found')
    locations = record_library_pickup_locations(holding)
    return jsonify({
       'locations': locations
    })


@api_blueprint.route('/<pid>/availability', methods=['GET'])
def holding_availability(pid):
    """HTTP GET request for holding availability."""
    if holding := Holding.get_record_by_pid(pid):
        return jsonify({
            'available': holding.is_available()
        })
    abort(404)
