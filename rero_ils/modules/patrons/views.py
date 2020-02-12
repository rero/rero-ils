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

from flask import Blueprint, current_app, flash, jsonify, render_template, \
    request
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_i18n.ext import current_i18n
from werkzeug.exceptions import NotFound

from .api import Patron
from .utils import user_has_patron
from ..items.api import Item
from ..libraries.api import Library
from ..loans.api import Loan, patron_profile_loans
from ..locations.api import Location

api_blueprint = Blueprint(
    'api_patrons',
    __name__,
    url_prefix='/patrons',
    template_folder='templates',
    static_folder='static',
)


blueprint = Blueprint(
    'patrons',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/patrons/logged_user', methods=['GET'])
# @check_permission
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
            'baseUrl': current_app.config.get(
                'RERO_ILS_APP_BASE_URL',
                ''
            ),
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
    visible_when=user_has_patron
)
def profile(viewcode):
    """Patron Profile Page."""
    patron = Patron.get_patron_by_user(current_user)
    if patron is None:
        raise NotFound()
    if request.method == 'POST':
        loan = Loan.get_record_by_pid(request.values.get('loan_pid'))
        item = Item.get_record_by_pid(loan.get('item_pid'))
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

    return render_template(
        'rero_ils/patron_profile.html',
        record=patron,
        checkouts=checkouts,
        pendings=requests,
        history=history,
        viewcode=viewcode
    )


@blueprint.app_template_filter('get_patron_from_barcode')
def get_patron_from_barcode(value):
    """Get patron from barcode."""
    return Patron.get_patron_by_barcode(value)


@blueprint.app_template_filter('get_patron_from_checkout_item_pid')
def get_patron_from_checkout_item_pid(item_pid):
    """Get patron from a checked out item pid."""
    from invenio_circulation.api import get_loan_for_item
    patron_pid = get_loan_for_item(item_pid)['patron_pid']
    return Patron.get_record_by_pid(patron_pid)


@blueprint.app_template_filter('get_checkout_loan_for_item')
def get_checkout_loan_for_item(item_pid):
    """Get patron from a checkout item pid."""
    from invenio_circulation.api import get_loan_for_item
    return get_loan_for_item(item_pid)


@blueprint.app_template_filter('get_patron_from_pid')
def get_patron_from_pid(patron_pid):
    """Get patron from pid."""
    return Patron.get_record_by_pid(patron_pid)


@blueprint.app_template_filter('get_location_name_from_pid')
def get_location_name_from_pid(location_pid):
    """Get location from pid."""
    return Location.get_record_by_pid(location_pid)['name']
