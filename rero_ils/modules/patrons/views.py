# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

import copy
import datetime
import re

from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from flask_babel import format_currency
from flask_babel import lazy_gettext
from flask_babel import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from flask_security import utils as security_utils
from invenio_i18n.ext import current_i18n
from invenio_oauth2server.decorators import require_api_auth

from rero_ils.modules.decorators import check_logged_as_librarian, \
    check_logged_as_patron, check_logged_user_authentication
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.loans.api import get_loans_stats_by_patron_pid, \
    get_overdue_loans
from rero_ils.modules.loans.utils import sum_for_fees
from rero_ils.modules.locations.api import Location
from rero_ils.modules.organisations.dumpers import OrganisationLoggedUserDumper
from rero_ils.modules.patron_transactions.utils import \
    get_transactions_total_amount_for_patron
from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch
from rero_ils.modules.patrons.api import Patron, PatronsSearch, \
    current_librarian, current_patrons
from rero_ils.modules.patrons.permissions import get_allowed_roles_management
from rero_ils.modules.patrons.utils import user_has_patron
from rero_ils.modules.permissions import expose_actions_need_for_user
from rero_ils.modules.users.api import User
from rero_ils.modules.utils import extracted_data_from_ref, get_base_url
from rero_ils.utils import remove_empties_from_dict

api_blueprint = Blueprint(
    'api_patrons',
    __name__,
    url_prefix='/patrons',
    template_folder='templates',
    static_folder='static',
)


_PID_REGEX = re.compile(r'NOT\s+pid:\s*(\w+)\s*')
_EMAIL_REGEX = re.compile(r'email:"\s*(.*?)\s*"')
_USERNAME_REGEX = re.compile(r'username:"\s*(.*?)\s*"')


@api_blueprint.route('/<patron_pid>/circulation_informations', methods=['GET'])
@check_logged_as_librarian
def patron_circulation_informations(patron_pid):
    """Get the circulation statistics and info messages about a patron."""
    patron = Patron.get_record_by_pid(patron_pid)
    if not patron:
        abort(404, 'Patron not found')
    preview_amount = sum(
        sum_for_fees(loan.get_overdue_fees)
        for loan in get_overdue_loans(patron.pid)
    )
    engaged_amount = get_transactions_total_amount_for_patron(
        patron.pid, status='open')
    statistics = get_loans_stats_by_patron_pid(patron_pid)
    statistics['ill_requests'] = ILLRequestsSearch() \
        .get_ill_requests_total_for_patron(patron_pid)
    return jsonify({
        'fees': {
          'engaged': engaged_amount,
          'preview': preview_amount
        },
        'statistics': statistics,
        'messages': patron.get_circulation_messages()
    })


@api_blueprint.route('/<patron_pid>/overdues/preview', methods=['GET'])
@login_required
def patron_overdue_preview_api(patron_pid):
    """Get all overdue preview linked to a patron."""
    data = []
    for loan in get_overdue_loans(patron_pid):
        fees = loan.get_overdue_fees
        fees = [(fee[0], fee[1].isoformat()) for fee in fees]
        total_amount = sum_for_fees(fees)
        if total_amount > 0:
            data.append({
                'loan': loan.dumps(),
                'fees': {'total': total_amount, 'steps': fees}
            })
    return jsonify(data)


blueprint = Blueprint(
    'patrons',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/patrons/logged_user', methods=['GET'])
def logged_user():
    """Current logged user information in JSON."""
    config = current_app.config
    data = {
        'permissions': expose_actions_need_for_user(),
        'settings': {
            'language': current_i18n.locale.language,
            'globalView': config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'),
            'baseUrl': get_base_url(),
            'agentLabelOrder': config.get('RERO_ILS_AGENTS_LABEL_ORDER', {}),
            'agentSources': config.get('RERO_ILS_AGENTS_SOURCES', []),
            'operationLogs': config.get('RERO_ILS_ENABLE_OPERATION_LOG', []),
            'documentAdvancedSearch': config.get(
                'RERO_ILS_APP_DOCUMENT_ADVANCED_SEARCH', False),
            'userProfile': {
                'readOnly': config.get(
                    'RERO_PUBLIC_USERPROFILES_READONLY', False),
                'readOnlyFields': config.get(
                    'RERO_PUBLIC_USERPROFILES_READONLY_FIELDS', []),
            }
        }
    }
    if not current_user.is_authenticated:
        return jsonify(data)

    user = User.get_record(current_user.id).dumps_metadata()
    user['id'] = current_user.id
    data = {**data, **user, 'patrons': []}
    for patron in Patron.get_patrons_by_user(current_user):
        patron.pop('$schema', None)
        patron.pop('user_id', None)
        patron.pop('notes', None)
        patron['organisation'] = patron.organisation.dumps(
            dumper=OrganisationLoggedUserDumper())
        patron['libraries'] = [
            {'pid': pid}
            for pid in patron.manageable_library_pids
        ]
        data['patrons'].append(patron)

    return jsonify(data)


@blueprint.route('/<string:viewcode>/patrons/profile', methods=['GET', 'POST'])
@check_logged_as_patron
@register_menu(
    blueprint,
    'settings.patron_profile',
    lazy_gettext('%(icon)s My loans', icon='<i class="fa fa-book fa-fw"></i>'),
    visible_when=user_has_patron,
    id="my-profile-menu",
    order=-1
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.patron_profile', _('Patron Profile')
)
def profile(viewcode):
    """Patron Profile Page."""
    return render_template('rero_ils/patron_profile.html', viewcode=viewcode)


@blueprint.app_template_filter('format_currency')
def format_currency_filter(value, currency):
    """Format currency with current locale."""
    if value:
        return format_currency(value, currency)


@api_blueprint.route('/roles_management_permissions', methods=['GET'])
@check_logged_as_librarian
def get_roles_management_permissions():
    """Get the roles that current logged user could manage."""
    return jsonify({
        'allowed_roles': get_allowed_roles_management()
    })


@blueprint.app_template_filter('get_patron_from_checkout_item_pid')
def get_patron_from_checkout_item_pid(item_pid):
    """Get patron from a checked out item pid."""
    from invenio_circulation.api import get_loan_for_item
    patron_pid = get_loan_for_item(item_pid_to_object(item_pid))['patron_pid']
    return Patron.get_record_by_pid(patron_pid)


@blueprint.app_template_filter('get_checkout_loan_for_item')
def get_checkout_loan_for_item(item_pid):
    """Get patron from a checkout item pid."""
    from invenio_circulation.api import get_loan_for_item
    return get_loan_for_item(item_pid_to_object(item_pid))


@blueprint.app_template_filter('get_patron_from_pid')
def get_patron_from_pid(patron_pid):
    """Get patron from pid."""
    return Patron.get_record_by_pid(patron_pid)


@blueprint.app_template_filter('get_location_name_from_pid')
def get_location_name_from_pid(location_pid):
    """Get location from pid."""
    return Location.get_record_by_pid(location_pid)['name']


@api_blueprint.route('/<string:patron_pid>/messages', methods=['GET'])
@check_logged_user_authentication
def get_messages(patron_pid):
    """Get messages for the current user."""
    patron = Patron.get_record_by_pid(patron_pid)
    messages = patron.get_circulation_messages(True)
    if patron.pending_subscriptions:
        messages.append({
            'type': 'warning',
            'content': _('You have a pending subscription fee.')
        })
    for note in patron.get('notes', []):
        if note.get('type') == 'public_note':
            messages.append({
                'type': 'warning',
                'content': note.get('content')
            })
    bootstrap_alert_mapping = {
        'error': 'danger'
    }
    for message in messages:
        msg_type = message['type']
        message['type'] = bootstrap_alert_mapping.get(msg_type, msg_type)
    return jsonify(messages)


@api_blueprint.route('/authenticate', methods=['POST'])
@check_logged_as_librarian
def patron_authenticate():
    """Patron authenticate.

    :param username - user username
    :param password - user password
    :returns: The patron's information.
    """
    json = flask_request.get_json()
    if not json or 'username' not in json or 'password' not in json:
        abort(400)
    username = json['username']
    password = json['password']
    # load user
    user = User.get_by_username_or_email(username)
    if not user:
        abort(404, 'User not found.')
    # load patron
    organisation_pid = current_librarian.organisation_pid
    result = PatronsSearch()\
        .filter('term', user_id=user.user.id)\
        .filter('term', organisation__pid=organisation_pid)\
        .scan()
    try:
        patron = next(result).to_dict()
    except StopIteration:
        abort(404, 'User not found.')
    # Validate password
    if not security_utils.verify_password(password, user.user.password):
        abort(401, 'Identification error.')
    patron_data = patron.get('patron', {})
    if not patron_data:
        abort(404, 'User not found.')
    patron_type_result = PatronTypesSearch()\
        .filter('term', pid=patron_data.get('type', {}).get('pid'))\
        .source(includes=['code'])\
        .scan()
    try:
        patron_type = next(patron_type_result).to_dict()
    except StopIteration:
        abort(404)
    return jsonify(remove_empties_from_dict({
        'fullname': patron.get('first_name') + ' ' + patron.get('last_name'),
        'street': patron.get('street'),
        'postal_code': patron.get('postal_code'),
        'city': patron.get('city'),
        'phone': patron.get('home_phone'),
        'email': patron.get('email'),
        'birth_date': patron.get('birth_date'),
        'patron_type': patron_type.get('code'),
        'expiration_date': patron_data.get('expiration_date'),
        'blocked': patron_data.get('blocked', False),
        'blocked_note': patron_data.get('blocked_note'),
        'notes': list(filter(
            lambda note: note.get('type') == 'staff_note',
            patron.get('notes', [])
        ))
    }))


@api_blueprint.route('/info', methods=['GET'])
@require_api_auth()
def info():
    """Get patron info."""
    token_scopes = flask_request.oauth.access_token.scopes

    def get_main_patron(patrons):
        """Return the main patron.

        :param patrons: List of patrons.
        :returns: The main patron.
        """
        # TODO: Find a way to determine which is the main patron.
        return patrons[0]

    def get_institution_code(institution):
        """Get the institution code for a given institution.

        Special transformation for `nj`.

        :param institution: Institution object.
        :returns: Code for the institution.
        """
        # TODO: make this non rero specific using a configuration
        return institution['code'] if institution['code'] != 'nj' else 'rbnj'

    user = User.get_record(current_user.id).dumps_metadata()

    # Process for all patrons
    patrons = copy.deepcopy(current_patrons)
    for patron in patrons:
        patron['institution'] = patron.organisation
        patron['patron']['type'] = PatronType.get_record_by_pid(
            extracted_data_from_ref(patron['patron']['type']['$ref']))

    # Birthdate
    data = {}
    birthdate = current_user.user_profile.get('birth_date')
    if 'birthdate' in token_scopes and birthdate:
        data['birthdate'] = birthdate
    # Full name
    name_parts = [
        current_user.user_profile.get('last_name', '').strip(),
        current_user.user_profile.get('first_name', '').strip()
    ]
    fullname = ', '.join(filter(None, name_parts))
    if 'fullname' in token_scopes and fullname:
        data['fullname'] = fullname

    # No patrons found for user
    if not patrons:
        return jsonify(data)

    # Get the main patron
    patron = get_main_patron(patrons)
    # Barcode
    if patron.get('patron', {}).get('barcode'):
        data['barcode'] = patron['patron']['barcode'][0]
    # Patron types
    if 'patron_types' in token_scopes:
        patron_types = []
        for patron in patrons:
            info = {}
            patron_type_code = patron.get(
                'patron', {}).get('type', {}).get('code')
            if patron_type_code:
                info['patron_type'] = patron_type_code
            if patron.get('institution'):
                info['institution'] = get_institution_code(
                    patron['institution'])
            if patron.get('patron', {}).get('expiration_date'):
                info['expiration_date'] = datetime.datetime.strptime(
                    patron['patron']['expiration_date'],
                    '%Y-%m-%d').isoformat()
            if info:
                patron_types.append(info)
        if patron_types:
            data['patron_types'] = patron_types

    return jsonify(data)


@blueprint.add_app_template_global
def patron_message():
    """Get patron message."""
    if not current_patrons:
        return
    data = {
        'show_info': False,
        'data': {}
    }
    for patron in current_patrons:
        if (patron.is_blocked or patron.is_expired):
            data['show_info'] = True
        organisation = patron.organisation
        data['data'][organisation['code']] = {
            'name': organisation['name'],
            'blocked': {
                'is_blocked': patron.is_blocked,
                'message': patron.get_blocked_message(public=True)
            },
            'is_expired': patron.is_expired
        }
    return data
