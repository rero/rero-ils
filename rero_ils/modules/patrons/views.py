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
from functools import wraps

from elasticsearch_dsl import Q
from flask import Blueprint, abort, current_app, flash, jsonify, \
    render_template, request
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_i18n.ext import current_i18n
from werkzeug.exceptions import NotFound

from .api import Patron, PatronsSearch
from .permissions import get_allowed_roles_management
from .utils import user_has_patron
from ..items.api import Item
from ..items.utils import item_pid_to_object
from ..libraries.api import Library
from ..loans.api import Loan, patron_profile_loans
from ..locations.api import Location
from ..utils import get_base_url
from ...permissions import login_and_librarian

api_blueprint = Blueprint(
    'api_patrons',
    __name__,
    url_prefix='/patrons',
    template_folder='templates',
    static_folder='static',
)


_PID_REGEX = re.compile(r'NOT\s+pid:\s*(\w+)\s*')
_EMAIL_REGEX = re.compile(r'email:"\s*(.*?)\s*"')


def check_permission(fn):
    """Decorate to check permission access.

    The access is allow when the connected user is a librarian.
    """
    @wraps(fn)
    def is_logged_librarian(*args, **kwargs):
        """Decorated view."""
        login_and_librarian()
        return fn(*args, **kwargs)
    return is_logged_librarian


@api_blueprint.route('/count/', methods=['GET'])
@check_permission
def number_of_patrons():
    """Returns the number of patrons matching the query.

    The query should be one of the following forms:
      - `/api/patrons/count/?q=email:"test@test.ch"
      - `/api/patrons/count/?q=email:"test@test.ch" NOT pid:1

    :return: The number of existing user account corresponding to the given
    email.
    :rtype: A JSON of the form:{"hits": {"total": 1}}
    """
    query = request.args.get('q')
    email = _EMAIL_REGEX.search(query)
    if not email:
        abort(400)
    email = email.group(1)
    s = PatronsSearch().query('match', email__analyzed=email)
    exclude_pid = _PID_REGEX.search(query)
    if exclude_pid:
        exclude_pid = exclude_pid.group(1)
        s = s.filter('bool', must_not=[Q('term', pid=exclude_pid)])
    response = dict(hits=dict(total=s.count()))
    return jsonify(response)


blueprint = Blueprint(
    'patrons',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/patrons/logged_user', methods=['GET'])
def logged_user():
    """Current logged user informations in JSON."""
    patron = Patron.get_patron_by_user(current_user)
    if patron and 'resolve' in request.args:
        patron = patron.replace_refs()
        patron = patron.dumps()
        if patron.get('library'):
            library = Library.get_record_by_pid(
                patron['library']['pid']
            ).replace_refs()
            patron['library']['organisation'] = {
                'pid': library['organisation']['pid']
            }
    personsLabelOrder = current_app.config.get(
        'RERO_ILS_PERSONS_LABEL_ORDER', {}
    )
    data = {
        'settings': {
            'language': current_i18n.locale.language,
            'global_view': current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'),
            'baseUrl': get_base_url(),
            'personsLabelOrder': personsLabelOrder.get(
                current_i18n.locale.language,
                personsLabelOrder.get(personsLabelOrder.get('fallback')))
        }
    }
    if patron:
        data['metadata'] = patron
    return jsonify(data)


@blueprint.route('/global/patrons/profile', defaults={'viewcode': 'global'},
                 methods=['GET', 'POST'])
@blueprint.route('/<string:viewcode>/patrons/profile')
@login_required
@register_menu(
    blueprint,
    'main.profile.profile',
    _('%(icon)s Profile', icon='<i class="fa fa-user fa-fw"></i>'),
    visible_when=user_has_patron,
    id="my-account-menu"
)
def profile(viewcode):
    """Patron Profile Page."""
    tab = 'checkouts'
    patron = Patron.get_patron_by_user(current_user)
    if patron is None:
        raise NotFound()
    if request.method == 'POST':
        loan = Loan.get_record_by_pid(request.values.get('loan_pid'))
        item = Item.get_record_by_pid(loan.get('item_pid', {}).get('value'))
        if request.form.get('type') == 'cancel':
            tab = 'pendings'
            cancel_params = {
                'pid': loan.pid,
                'transaction_location_pid': item.location_pid,
                'transaction_user_pid': patron.pid
            }
            try:
                item.cancel_item_request(**cancel_params)
                flash(_('The request for item %(item_id)s has been canceled.',
                        item_id=item.pid), 'success')
            except Exception:
                flash(_('Error during the cancellation of the request of \
                item %(item_id)s.', item_id=item.pid), 'danger')
        elif request.form.get('type') == 'renew':
            data = {
                'item_pid': item.pid,
                'pid': request.values.get('loan_pid'),
                'transaction_location_pid': item.location_pid
            }
            try:
                item.extend_loan(**data)
                flash(_('The item %(item_id)s has been renewed.',
                        item_id=item.pid), 'success')
            except Exception:
                flash(_('Error during the renewal of the item %(item_id)s.',
                        item_id=item.pid), 'danger')

    checkouts, requests, history = patron_profile_loans(patron.pid)

    # patron alert list
    #   each alert dictionary key represent an alert category (subscription,
    #   fees, blocked, ...). For each category, we define a bootstrap level
    #   (https://getbootstrap.com/docs/4.0/components/alerts/) and a list of
    #   message. Each message will be displayed into a separate alert box.
    alerts = {}
    pending_subscriptions = patron.get_pending_subscriptions()
    if pending_subscriptions:
        alerts['subscriptions'] = {
            'messages': map(
                lambda sub: _('You have a pending subscription fee.'),
                pending_subscriptions
            ),
            'level': 'warning'  # bootstrap alert level
        }
    if patron.get('blocked'):
        alerts['blocking'] = {
            'messages': [
                _('Your account is currently blocked. Reason: %(reason)s',
                    reason=patron.get('blocked_note', ''))
            ],
            'level': 'danger'
        }

    return render_template(
        'rero_ils/patron_profile.html',
        record=patron,
        checkouts=checkouts,
        alerts=alerts,
        pendings=requests,
        history=history,
        viewcode=viewcode,
        tab=tab
    )


@api_blueprint.route('/roles_management_permissions', methods=['GET'])
@check_permission
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
