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
from ..patrons.api import Patron
from .api import Item
from .models import ItemStatus
from .utils import commit_item, item_from_web_request

blueprint = Blueprint(
    'items',
    __name__,
    url_prefix='/items',
    template_folder='templates',
    static_folder='static',
)


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


@blueprint.route("/return", methods=['POST', 'PUT'])
@check_authentication
def return_item():
    """HTTP request for Item return action."""
    try:
        data = request.get_json()
        item = item_from_web_request(data)
        patron = Patron.get_patron_by_email(current_user.email)
        item.return_item(patron['member_pid'])
        commit_item(item)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500


@blueprint.route("/validate", methods=['POST', 'PUT'])
@check_authentication
def validate_item_request():
    """HTTP request for Item request validation action."""
    try:
        data = request.get_json()
        item = item_from_web_request(data)
        item.validate_item_request(**data)
        commit_item(item)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500


@blueprint.route("/receive", methods=['POST', 'PUT'])
@check_authentication
def receive_item():
    """HTTP request for receive item action."""
    try:
        data = request.get_json()
        patron = Patron.get_patron_by_email(current_user.email)
        member_pid = patron['member_pid']
        item = item_from_web_request(data)
        item.receive_item(member_pid, **data)
        commit_item(item)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500


@blueprint.route("/loan", methods=['POST', 'PUT'])
@check_authentication
def loan_item():
    """HTTP request for Item loan action."""
    try:
        data = request.get_json()
        item = item_from_web_request(data)
        item.loan_item(**data)
        commit_item(item)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500


@blueprint.route("/return_missing", methods=['POST', 'PUT'])
@check_authentication
def return_missing_item():
    """HTTP request for Item return_missing action."""
    try:
        data = request.get_json()
        item = item_from_web_request(data)
        item.return_missing_item()
        commit_item(item)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500


@blueprint.route("/extend", methods=['POST', 'PUT'])
@check_authentication
def extend_loan():
    """HTTP request for Item due date extend action."""
    try:
        data = request.get_json()
        requested_end_date = data.get('end_date')
        renewal_count = data.get('renewal_count')
        item = item_from_web_request(data)
        item.extend_loan(requested_end_date=requested_end_date,
                         renewal_count=renewal_count)
        commit_item(item)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500


@blueprint.route("/request/<pid_value>/<member>", methods=['GET'])
@check_authentication_for_request
def request_item(pid_value, member):
    """HTTP GET request for Item request action."""
    try:
        patron = Patron.get_patron_by_email(current_user.email)
        patron_barcode = patron['barcode']
        item = Item.get_record_by_pid(pid_value)
        doc = DocumentsWithItems.get_document_by_itemid(item.id)
        request_datetime = pytz.utc.localize(datetime.now()).isoformat()
        item.request_item(
            patron_barcode=patron_barcode,
            pickup_member_pid=member,
            request_datetime=request_datetime
        )
        commit_item(item)
        flash(_('The item %s has been requested.' % pid_value), 'success')
        return_value = redirect(
            url_for('invenio_records_ui.doc', pid_value=doc['pid'])
        )
        return redirect(
            url_for('invenio_records_ui.doc', pid_value=doc['pid'])
        )
    except Exception as e:
        return jsonify({'status': 'error: %s' % e}), 500
        flash(_('Something went wrong'), 'danger')


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
        current_app._get_current_object(),
        pid=pid,
        record=record,
    )
    document = DocumentsWithItems.get_document_by_itemid(record.id)
    return render_template(
        template,
        pid=pid,
        record=record,
        document=document
    )


@blueprint.app_template_filter()
def item_status_text(item, format='medium', locale='en'):
    """Text for item status."""
    if item.available:
        text = _('available')
        if item.get('item_type') == "on_site_consultation":
            text += ' ({0})'.format(_("on_site consultation"))
    else:
        text = _('not available')
        if item.status == ItemStatus.ON_LOAN:
            due_date = format_date_filter(
                item.get_item_end_date(),
                format=format,
                locale=locale
            )
            text += ' ({0} {1})'.format(_('due until'), due_date)
        elif item.number_of_item_requests() > 0:
            text += ' ({0})'.format(_('requested'))
        elif item.status == ItemStatus.IN_TRANSIT:
            text += ' ({0})'.format(_(ItemStatus.IN_TRANSIT))
    return text
