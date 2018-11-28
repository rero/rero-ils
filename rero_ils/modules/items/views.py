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

from datetime import datetime
from functools import wraps

import pytz
from flask import Blueprint, current_app, flash, jsonify, redirect, \
    render_template, request, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from ...filter import format_date_filter
from ...permissions import record_edit_permission, request_item_permission
from ..documents_items.api import DocumentsWithItems
from ..patrons.api import Patron, current_patron
from .api import Item
from .models import ItemStatus

blueprint = Blueprint(
    'items',
    __name__,
    url_prefix='/items/loan',
    template_folder='templates',
    static_folder='static',
)


def check_authentication_for_request(func):
    """Decorator to check authentication for item requests HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not request_item_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)

    return decorated_view


def check_authentication(func):
    """Decorator to check authentication for items HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not record_edit_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return func(*args, **kwargs)

    return decorated_view


@blueprint.route('/request/<item_pid_value>/<location>', methods=['GET'])
@check_authentication_for_request
def request_item(item_pid_value, location):
    """HTTP GET request for Item request action."""
    try:
        patron = Patron.get_patron_by_email(current_user.email)
        item = Item.get_record_by_pid(item_pid_value)
        location_pid = item.get('location_pid')
        doc = DocumentsWithItems.get_document_by_itemid(item.id)
        transaction_date = pytz.utc.localize(datetime.now()).isoformat()
        item.request_item(
            patron_pid=patron.pid,
            pickup_location_pid=location,
            transaction_date=transaction_date,
            document_pid=doc.pid,
            transaction_user_pid=patron.pid,
            transaction_location_pid=location_pid,
        )
        flash(_('The item %s has been requested.' % item_pid_value), 'success')
        return redirect(
            url_for("invenio_records_ui.doc", pid_value=doc['pid']))
    except Exception as e:
        return (
            jsonify(
                {
                    "status': 'error: {error} {patron}".format(
                        error=e, patron=patron.dumps()
                    )
                }
            ),
            500,
        )


@blueprint.route('/checkout', methods=['POST', 'PUT'])
@check_authentication
def loan_item():
    """HTTP request for Item checkout action."""
    try:
        data = request.get_json()
        item = Item.get_record_by_pid(data.get('item_pid'))
        loan = item.loan_item(**data)
        return jsonify(loan.dumps())
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route('/automatic_checkin', methods=['POST', 'PUT'])
@check_authentication
def automatic_checkin():
    """HTTP request for Item circulation actions."""
    try:
        patron = current_patron.dumps()
        data = request.get_json()
        item = Item.get_item_by_barcode(data.get('item_barcode'))
        params = dict(patron=patron)
        params['transaction_user_pid'] = patron.get(
            'pid'
        )
        params['transaction_location_pid'] = patron.get(
            'circulation_location_pid'
        )
        loan = item.automatic_checkin(**params)
        return jsonify(loan)
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route("/checkin", methods=['POST', 'PUT'])
@check_authentication
def return_item():
    """HTTP request for Item return action."""
    try:
        data = request.get_json()
        item = Item.get_record_by_pid(data.get('item_pid'))
        params = dict(loan_pid=data['loan_pid'])
        loan = item.return_item(**params)
        return jsonify(loan.dumps())
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route("/cancel", methods=['POST', 'PUT'])
@check_authentication
def cancel():
    """HTTP request for cancel action."""
    try:
        data = request.get_json()
        params = dict(loan_pid=data['loan_pid'])
        if data.get('item_pid'):
            item = Item.get_record_by_pid(data.get('item_pid'))
            loan = item.cancel_item_loan(**params)
        else:
            loan = item.cancel_loan(**params)
        return jsonify(loan.dumps())
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route('/validate', methods=['POST', 'PUT'])
@check_authentication
def validate_item_request():
    """HTTP request for Item request validation action."""
    try:
        data = request.get_json()
        item = Item.get_record_by_pid(data.get('item_pid'))
        loan = item.validate_item_request(**data)
        return jsonify(loan.dumps())
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route('/receive', methods=['POST', 'PUT'])
@check_authentication
def receive_item():
    """HTTP request for receive item action."""
    try:
        data = request.get_json()
        params = dict(loan_pid=data['loan_pid'])
        item = Item.get_record_by_pid(data.get('item_pid'))
        loan = item.receive_item(**params)
        return jsonify(loan.dumps())
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route('/return_missing', methods=['POST', 'PUT'])
@check_authentication
def return_missing_item():
    """HTTP request for Item return_missing action."""
    try:
        data = request.get_json()
        item = Item.get_record_by_pid(data.get('item_pid'))
        loan = item.return_missing_item()
        return jsonify(loan)
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


@blueprint.route('/extend', methods=['POST', 'PUT'])
@check_authentication
def extend_loan():
    """HTTP request for Item due date extend action."""
    try:
        data = request.get_json()
        item = Item.get_record_by_pid(data.get('item_pid'))
        loan = item.extend_loan(**data)
        return jsonify(loan.dumps())
    except Exception as e:
        return jsonify({'status': 'error: {error}'.format(error=e)}), 500


def item_view_method(pid, record, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record
    )
    document = DocumentsWithItems.get_document_by_itemid(record.id)
    return render_template(template, pid=pid, record=record, document=document)


@blueprint.app_template_filter()
def item_status_text(item, format='medium', locale='en'):
    """Text for item status."""
    if item.available:
        text = _('available')
        if item.dumps().get('item_type') == 'on_site_consultation':
            text += ' ({0})'.format(_('on_site consultation'))
    else:
        text = _('not available')
        if item.status == ItemStatus.ON_LOAN:
            due_date = format_date_filter(
                item.get_item_end_date(), format=format, locale=locale
            )
            text += ' ({0} {1})'.format(_('due until'), due_date)
        elif item.number_of_item_requests() > 0:
            text += ' ({0})'.format(_('requested'))
        elif item.status == ItemStatus.IN_TRANSIT:
            text += ' ({0})'.format(_(ItemStatus.IN_TRANSIT))
    return text


@blueprint.route('/requested_loans/<library_pid_value>', methods=['GET'])
@check_authentication
def requested_loans(library_pid_value):
    """HTTP GET request for requested loans for a library."""
    from ..loans.api import get_pendings_by_library_pid, item_has_active_loans
    loans = list(get_pendings_by_library_pid(library_pid_value))
    items_to_validate = []
    requests = []
    item_with_active_loans = []
    for loan in loans:
        item_pid = loan.item_pid
        if (
            item_pid not in item_with_active_loans and
            item_pid not in items_to_validate
        ):
            if item_has_active_loans(item_pid):
                item_with_active_loans.append(item_pid)
            else:
                requests.append(loan.to_dict())
                items_to_validate.append(item_pid)
    return jsonify(requests)
