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

import re

from flask import Blueprint, abort, current_app, jsonify, render_template
from flask_babelex import format_currency
from flask_babelex import gettext as _
from flask_babelex import lazy_gettext
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_i18n.ext import current_i18n

from .api import Patron
from .permissions import get_allowed_roles_management
from .utils import user_has_patron
from ..decorators import check_logged_as_librarian, check_logged_as_patron, \
    check_logged_user_authentication
from ..items.utils import item_pid_to_object
from ..loans.api import get_loans_stats_by_patron_pid, get_overdue_loans
from ..loans.utils import sum_for_fees
from ..locations.api import Location
from ..patron_transactions.api import PatronTransaction
from ..users.api import User
from ..utils import get_base_url

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
    preview_amount = 0
    for loan in get_overdue_loans(patron.pid):
        preview_amount += sum_for_fees(loan.get_overdue_fees)
    engaged_amount = PatronTransaction\
        .get_transactions_total_amount_for_patron(patron.pid, status='open')
    return jsonify({
        'fees': {
          'engaged': engaged_amount,
          'preview': preview_amount
        },
        'statistics': get_loans_stats_by_patron_pid(patron_pid),
        'messages': patron.get_circulation_messages()
    })


@api_blueprint.route('/<patron_pid>/overdues/preview', methods=['GET'])
@login_required
def patron_overdue_preview_api(patron_pid):
    """Get all overdue preview linked to a patron."""
    data = []
    for loan in get_overdue_loans(patron_pid):
        fees = loan.get_overdue_fees
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
    """Current logged user informations in JSON."""
    data = {
        'settings': {
            'language': current_i18n.locale.language,
            'globalView': current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'),
            'baseUrl': get_base_url(),
            'contributionAgentTypes': current_app.config.get(
                'RERO_ILS_CONTRIBUTIONS_AGENT_TYPES', {}),
            'contributionsLabelOrder': current_app.config.get(
                'RERO_ILS_CONTRIBUTIONS_LABEL_ORDER', {}),
            'contributionSources': current_app.config.get(
                'RERO_ILS_CONTRIBUTIONS_SOURCES', []
            ),
            'operationLogs': current_app.config.get(
                'RERO_ILS_ENABLE_OPERATION_LOG', []
            ),
            'librarianRoles': current_app.config.get(
                'RERO_ILS_LIBRARIAN_ROLES', []
            )
        }
    }
    if not current_user.is_authenticated:
        return jsonify(data)

    user = User.get_by_id(current_user.id).dumpsMetadata()
    user['id'] = current_user.id
    data = {**data, **user}
    data['patrons'] = []

    for patron in Patron.get_patrons_by_user(current_user):
        del patron['$schema']
        del patron['user_id']
        # The notes are loaded by another way
        if 'notes' in patron:
            del patron['notes']
        organisation = patron.get_organisation()
        patron['organisation'] = {
            'pid': organisation.get('pid'),
            'name': organisation.get('name'),
            'code': organisation.get('code'),
            'currency': organisation.get('default_currency')
        }
        patron = patron.replace_refs()
        for index, library in enumerate(patron.get('libraries', [])):
            patron['libraries'][index] = {
                'pid': library['pid'],
                'organisation': {
                    'pid': organisation.get('pid')
                }
            }
        data['patrons'].append(patron)

    return jsonify(data)


@blueprint.route('/global/patrons/profile', defaults={'viewcode': 'global'},
                 methods=['GET', 'POST'])
@blueprint.route('/<string:viewcode>/patrons/profile')
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
    return render_template('rero_ils/patron_profile.html')


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


@blueprint.app_template_filter('get_patron_from_barcode')
def get_patron_from_barcode(value):
    """Get patron from barcode."""
    return Patron.get_patron_by_barcode(value)


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
    if patron.get_pending_subscriptions():
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
