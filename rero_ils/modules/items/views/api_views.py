# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
from elasticsearch_dsl import A, Q
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from flask_login import current_user
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.errors import CirculationException, \
    MissingRequiredParameterError
from jinja2 import TemplateNotFound, UndefinedError
from werkzeug.exceptions import NotFound

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.decorators import check_authentication, check_permission
from rero_ils.modules.documents.views import record_library_pickup_locations
from rero_ils.modules.errors import NoCirculationAction, \
    NoCirculationActionIsPermitted
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.dumpers import \
    CirculationDumper as LoanCirculationDumper
from rero_ils.modules.operation_logs.api import OperationLogsSearch
from rero_ils.modules.operation_logs.permissions import \
    search_action as op_log_search_action
from rero_ils.modules.patrons.api import Patron, current_librarian
from rero_ils.permissions import request_item_permission

from ..api import Item
from ..dumpers import CirculationActionDumper, ClaimIssueNotificationDumper
from ..models import ItemCirculationAction, ItemStatus
from ..permissions import late_issue_management as late_issue_management_action
from ..utils import get_recipient_suggestions, item_pid_to_object
from ...commons.exceptions import MissingDataException

api_blueprint = Blueprint(
    'api_item',
    __name__,
    url_prefix='/item'
)

blueprint = Blueprint(
    'items',
    __name__
)


def check_logged_user_authentication(func):
    """Decorator to check authentication for user HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        return func(*args, **kwargs)

    return decorated_view


def check_authentication_for_request(func):
    """Decorator to check authentication for item requests HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not request_item_permission.require().can():
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
            raise error
        except Exception as error:
            # raise error
            current_app.logger.error(str(error))
            return jsonify({'status': f'error: {error}'}), 500
    return decorated_view


def do_loan_jsonify_action(func):
    """Jsonify loan actions for non item methods.

    This method for the circulation actions that executed directly on the loan
    object and do not need to have direct access to the item object.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            data = deepcopy(flask_request.get_json())
            loan_pid = data.pop('pid', None)
            pickup_location_pid = data.get('pickup_location_pid', None)
            if not loan_pid or not pickup_location_pid:
                return jsonify({'status': 'error: Bad request'}), 400
            loan = Loan.get_record_by_pid(loan_pid)
            updated_loan = func(loan, data, *args, **kwargs)
            return jsonify(updated_loan)
        except NoCirculationActionIsPermitted as error:
            # The circulation specs do not allow updates on some loan states.
            abort(403, str(error))
    return decorated_view


def do_item_jsonify_action(func):
    """Jsonify loan actions for item methods.

    This method for the circulation actions that required access to the item
    object before executing the invenio-circulation logic.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            data = deepcopy(flask_request.get_json())
            item = Item.get_item_record_for_ui(**data)
            data.pop('item_barcode', None)

            if not item:
                abort(404)
            item_data, action_applied = \
                func(item, data, *args, **kwargs)
            for action, loan in action_applied.items():
                if loan:
                    action_applied[action] = loan.dumps(
                        LoanCirculationDumper())

            return jsonify({
                'metadata': item_data.dumps(CirculationActionDumper()),
                'action_applied': action_applied
            })
        except NoCirculationAction as error:
            return jsonify({'status': f'error: {str(error)}'}), 400
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
@do_item_jsonify_action
def patron_request(item, data):
    """HTTP POST request for Item request action by a patron.

    required parameters into the JSON data are:
        * item_pid
        * pickup_location_pid.
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the requested item resource.
    :param data: additional data used for the circ operation (as a dict).
    """
    # get the patron account of the same org of the location pid
    patron_pid = Patron.get_current_patron(item).pid
    data['patron_pid'] = patron_pid
    data['transaction_user_pid'] = patron_pid
    data['transaction_location_pid'] = data['pickup_location_pid']
    return item.request(**data)


@api_blueprint.route('/request', methods=['POST'])
@check_authentication
@do_item_jsonify_action
def librarian_request(item, data):
    """HTTP POST request for Item request action.

    required parameters into the JSON data are:
        * item_pid_value
        * pickup_location_pid
        * patron_pid
        * transaction_location_pid OR transaction_library_pid
        * transaction_user_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the requested item resource
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.request(**data)


@api_blueprint.route('/cancel_item_request', methods=['POST'])
@check_logged_user_authentication
@do_item_jsonify_action
def cancel_item_request(item, data):
    """HTTP GET request for cancelling and item request action.

    required parameters into the JSON data are:
        * pid (corresponding to loan pid)
        * transaction_location_pid OR transaction_library_pid
        * transaction_user_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the cancelled item resource
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.cancel_item_request(**data)


@api_blueprint.route('/checkout', methods=['POST'])
# @profile(sort_by='cumulative', lines_to_print=100)
@check_authentication
@do_item_jsonify_action
def checkout(item, data):
    """HTTP POST request for Item checkout action.

    required parameters into the JSON data are:
        * patron_pid
        * item_pid
        * transaction_location_pid
        * transaction_user_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the item resource on which checkout operation will be done.
    :param data: additional data used for the circ operation (as a dict).
    """
    data['override_blocking'] = flask_request.args.get(
        'override_blocking', False)
    return item.checkout(**data)


@api_blueprint.route("/checkin", methods=['POST'])
# @profile(sort_by='cumulative', lines_to_print=100)
@check_authentication
@do_item_jsonify_action
def checkin(item, data):
    """HTTP GET request for item return action.

    required parameters into the JSON data are:
        * item_pid OR item_barcode
        * transaction_location_pid OR transaction_library_pid
        * transaction_user_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the item resource on which checkin operation will be done.
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.checkin(**data)


@api_blueprint.route("/update_loan_pickup_location", methods=['POST'])
@check_authentication
@do_loan_jsonify_action
def update_loan_pickup_location(loan, data):
    """HTTP POST request for change a pickup location for a loan.

     required parameters into the JSON data are:
        * pid (the loan pid)
        * pickup_location_pid
    These json data are extracted by `do_loan_jsonify_action` decorator and
    used to load `loan` and `data` parameters.

    :param loan: the loan resource that will be updated
    :param data: additional data used for the circ operation (as a dict).
    """
    return loan.update_pickup_location(**data)


@api_blueprint.route('/validate_request', methods=['POST'])
@check_authentication
@do_item_jsonify_action
def validate_request(item, data):
    """HTTP GET request for Item request validation action.

    required parameters into the JSON data are:
        * pid (the loan pid)
        * transaction_location_pid OR transaction_library_pid
        * transaction_user_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the item resource on which validate operation will be done.
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.validate_request(**data)


@api_blueprint.route('/receive', methods=['POST'])
@check_authentication
@do_item_jsonify_action
def receive(item, data):
    """HTTP POST request for receive item action.

    required parameters into the JSON data are:
        * item_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the item resource on which receive operation will be done.
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.receive(**data)


@api_blueprint.route('/return_missing', methods=['POST'])
@check_authentication
@do_item_jsonify_action
def return_missing(item, data):
    """HTTP POST request for Item return_missing action.

    required parameters into the JSON data are:
        * item_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the item resource on which return operation will be done.
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.return_missing()


@api_blueprint.route('/extend_loan', methods=['POST'])
@check_logged_user_authentication
@do_item_jsonify_action
def extend_loan(item, data):
    """HTTP POST request for Item due date extend action.

    required parameters into the JSON data are:
        * item_pid
    These json data are extracted by `do_item_jsonify_action` decorator and
    used to load `item` and `data` parameters.

    :param item: the item resource on which extend operation will be done.
    :param data: additional data used for the circ operation (as a dict).
    """
    return item.extend_loan(**data)


@api_blueprint.route('/requested_loans/<library_pid>', methods=['GET'])
@check_authentication
@jsonify_error
def requested_loans(library_pid):
    """HTTP GET request for sorted requested loans for a library."""
    metadata = Loan.requested_loans_to_validate(library_pid)
    return jsonify({
        'hits': {
            'total': {
                'value': len(metadata)
            },
            'hits': metadata
        }
    })


@api_blueprint.route('/loans/<patron_pid>', methods=['GET'])
@check_authentication
@jsonify_error
def loans(patron_pid):
    """HTTP GET request for sorted loans for a patron pid."""
    sort_by = flask_request.args.get('sort')
    items = Item.get_checked_out_items(patron_pid=patron_pid, sort_by=sort_by)
    metadata = []
    for item in items:
        item_data = item.replace_refs()
        metadata.append({
            'item': {
                'pid': item.pid,
                'organisation_pid': item_data.get('organisation').get('pid'),
                'barcode': item.get('barcode')
            }
        })
    return jsonify({
        'hits': {
            'total': {
                'value': len(metadata)
            },
            'hits': metadata
        }
    })


@api_blueprint.route('/barcode/<item_barcode>', methods=['GET'])
@check_authentication
@jsonify_error
def item(item_barcode):
    """HTTP GET request for requested loans for a library item and patron."""
    item = Item.get_item_by_barcode(
        item_barcode, current_librarian.organisation_pid)
    if not item:
        abort(404)
    loan = get_loan_for_item(item_pid_to_object(item.pid))
    if loan:
        loan = Loan.get_record_by_pid(
            loan.get('pid')).dumps(LoanCirculationDumper())
    item_dumps = item.dumps(CirculationActionDumper())

    if patron_pid := flask_request.args.get('patron_pid'):
        patron = Patron.get_record_by_pid(patron_pid)
        organisation_pid = item.organisation_pid
        library_pid = item.library_pid
        patron_type_pid = patron.patron_type_pid
        item_type_pid = item.item_type_circulation_category_pid
        circ_policy = CircPolicy.provide_circ_policy(
            organisation_pid=organisation_pid,
            library_pid=library_pid,
            patron_type_pid=patron_type_pid,
            item_type_pid=item_type_pid
        )
        new_actions = []
        # If circulation policy doesn't allow checkout operation no need to
        # perform special check describe below.
        if circ_policy.can_checkout:
            for action in item_dumps.get('actions', []):
                if action == 'checkout':
                    if (
                        item.number_of_requests() > 0
                        and item.patron_request_rank(patron) == 1
                        or item.number_of_requests() <= 0
                    ):
                        new_actions.append(action)
                elif action == 'receive' and item.number_of_requests() == 0:
                    new_actions.append('checkout')
        item_dumps['actions'] = new_actions
    return jsonify({
        'metadata': {
            'item': item_dumps,
            'loan': loan
        }
    })


@api_blueprint.route('/<pid>/availability', methods=['GET'])
@jsonify_error
def item_availability(pid):
    """HTTP GET request for item availability."""
    item = Item.get_record_by_pid(pid)
    if not item:
        abort(404)
    data = dict(available=item.is_available())
    if flask_request.args.get('more_info'):
        extra = {
            'status': item['status'],
            'circulation_message': item.availability_text,
            'number_of_request': item.number_of_requests()
        }
        if not data['available'] and extra['status'] == ItemStatus.ON_LOAN:
            extra['due_date'] = item.get_item_end_date(format=None)
        data |= extra
    return jsonify(data)


@api_blueprint.route('/<item_pid>/can_request', methods=['GET'])
@check_logged_user_authentication
@jsonify_error
def can_request(item_pid):
    """REST-API endpoint to check if an item can be requested.

    Depending on query string argument, either only check if configuration
    allows the request of this item ; either if a librarian can request an
    item for a patron.

    `api/item/<item_pid>/can_request` :
         --> only check config
    `api/item/<item_pid>/can_request?library_pid=<library_pid>&patron_barcode=<barcode>`:
         --> check if the patron can request this item (check the cipo)
    """
    kwargs = {}
    item = Item.get_record_by_pid(item_pid)
    if not item:
        abort(404, 'Item not found')
    if patron_barcode := flask_request.args.get('patron_barcode'):
        kwargs['patron'] = Patron.get_patron_by_barcode(
            barcode=patron_barcode, org_pid=item.organisation_pid)
        if not kwargs['patron']:
            abort(404, 'Patron not found')
    if library_pid := flask_request.args.get('library_pid'):
        kwargs['library'] = Library.get_record_by_pid(library_pid)
        if not kwargs['library']:
            abort(404, 'Library not found')

    # ask item if the request is possible with these data.
    can, reasons = item.can(ItemCirculationAction.REQUEST, **kwargs)

    # check the `reasons_not_request` array. If it's empty, the request is
    # allowed ; if not the request is disallowed, and we need to return the
    # reasons why
    response = {'can': can}
    if reasons:
        response['reasons'] = {
            'others': {reason: True for reason in reasons}
        }
    return jsonify(response)


@api_blueprint.route('/<item_pid>/pickup_locations', methods=['GET'])
@check_logged_user_authentication
@jsonify_error
def get_pickup_locations(item_pid):
    """HTTP request to return the available pickup locations for an item.

    :param item_pid: the item pid
    """
    item = Item.get_record_by_pid(item_pid)
    if not item:
        abort(404, 'Item not found')
    locations = record_library_pickup_locations(item)
    return jsonify({
        'locations': locations
    })


@api_blueprint.route('/<item_pid>/stats', methods=['GET'])
@check_permission([op_log_search_action])
@jsonify_error
def stats(item_pid):
    """REST-API endpoint to get item statistics (total and past year).

    :param item_pid: the item pid
    """
    search = OperationLogsSearch()\
        .filter('term', loan__item__pid=item_pid)\
        .filter('term', record__type='loan')
    trigger = A(
        'terms',
        field='loan.trigger',
        aggs={
            'year': A('filter', Q('range', date={'gte': 'now-1y'}))
        }
    )
    search.aggs.bucket('trigger', trigger)
    search = search[:0]
    results = search.execute()
    output = {'total': {}, 'total_year': {}}
    for result in results.aggregations.trigger.buckets:
        output['total'][result.key] = result.doc_count
        output['total_year'][result.key] = result.year.doc_count
    # Add legacy checkout count
    if item := Item.get_record_by_pid(item_pid):
        legacy_count = item.get('legacy_checkout_count', 0)
        output['total'].setdefault('checkout', 0)
        output['total']['checkout'] += legacy_count
    return jsonify(output)


@api_blueprint.route('/<item_pid>/issue/claims/preview', methods=['GET'])
@check_permission([late_issue_management_action])
def claim_notification_preview(item_pid):
    """Get the preview of a claim issue notification content."""
    record = Item.get_record_by_pid(item_pid)
    if not record:
        abort(404, 'Item not found')
    if not record.is_issue:
        abort(400, 'Item isn\'t an issue')

    try:
        issue_data = record.dumps(dumper=ClaimIssueNotificationDumper())
    except (TypeError, MissingDataException) as exp:
        abort(500, str(exp))

    # update the claims issue counter ::
    #   As this is preview for next claim, we need to add 1 to the returned
    #   claim counter
    issue_data['claim_counter'] += 1
    language = issue_data.get('vendor', {}).get('language')

    response = {'recipient_suggestions': get_recipient_suggestions(record)}
    template_directory = 'email/claim_issue/'
    try:
        tmpl_file = f'{template_directory}/{language}.tpl.txt'
        response['preview'] = render_template(tmpl_file, issue=issue_data)
    except TemplateNotFound:
        # If the corresponding translated template isn't found, use the english
        # template as default template
        msg = f'None "claim_issue" template found for "{language}" language'
        current_app.logger.error(msg)
        response['message'] = [{'type': 'error', 'content': msg}]
        tmpl_file = f'{template_directory}/eng.tpl.txt'
        response['preview'] = render_template(tmpl_file, issue=issue_data)
    except UndefinedError as ue:
        abort(500, f'template generation failed : {str(ue)}')

    return jsonify(response)


@api_blueprint.route('/<item_pid>/issue/claims', methods=['POST'])
@check_permission([late_issue_management_action])
def claim_issue(item_pid):
    """API to claim an issue.

    Required parameters:
        recipients: the list of recipients (a list of dictionaries each
            containing the email and its type to, cc, reply_to, or bcc).

    :param item_pid: the item issue pid to claim.
    :returns: jsonify created claimed notification into `data` attribute.
    """
    item_issue = Item.get_record_by_pid(item_pid)
    if not item_issue:
        abort(404, 'Item not found')
    if not item_issue.is_issue:
        abort(400, 'Item isn\'t an issue')

    data = flask_request.get_json()
    if not (recipients := data.get('recipients')):
        abort(400, "Missing recipients emails.")
    notification = item_issue.claims(recipients)
    return jsonify({'data': notification})
