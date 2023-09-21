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

"""Blueprint used for AcqOrder API."""
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask import request as flask_request
from jinja2 import TemplateNotFound

from rero_ils.modules.decorators import check_logged_as_librarian, \
    jsonify_error

from .api import AcqOrder
from .dumpers import AcqOrderHistoryDumper, AcqOrderNotificationDumper
from .utils import get_history, get_recipient_suggestions

api_blueprint = Blueprint(
    'api_order',
    __name__,
    url_prefix='/acq_order',
    template_folder='templates'
)


@api_blueprint.route('/<order_pid>/history', methods=['GET'])
@check_logged_as_librarian
@jsonify_error
def order_history(order_pid):
    """Get the history of an acquisition order."""
    order = AcqOrder.get_record_by_pid(order_pid)
    if not order:
        abort(404, "Acquisition order not found")

    data = []
    for idx, acq_order in enumerate(get_history(order), 1):
        dump_data = acq_order.dumps(dumper=AcqOrderHistoryDumper())
        dump_data['order'] = idx
        data.append(dump_data)
    return jsonify(data)


@api_blueprint.route('/<order_pid>/acquisition_order/preview', methods=['GET'])
@check_logged_as_librarian
@jsonify_error
def order_notification_preview(order_pid):
    """Get the preview of an acquisition order notification content."""
    order = AcqOrder.get_record_by_pid(order_pid)
    if not order:
        abort(404, "Acquisition order not found")

    response = {'recipient_suggestions': get_recipient_suggestions(order)}
    order_data = order.dumps(dumper=AcqOrderNotificationDumper())
    language = order_data.get('vendor', {}).get('language')
    try:
        tmpl_file = f'rero_ils/vendor_order_mail/{language}.tpl.txt'
        response['preview'] = render_template(tmpl_file, order=order_data)
    except TemplateNotFound:
        # If the corresponding translated template isn't found, use the english
        # template as default template
        msg = 'None "vendor_order_mail" template found for ' \
              f'"{language}" language'
        current_app.logger.error(msg)
        response['message'] = [{'type': 'error', 'content': msg}]
        language = current_app.config.get(
            'RERO_ILS_APP_DEFAULT_LANGUAGE', 'eng')
        tmpl_file = f'rero_ils/vendor_order_mail/{language}.tpl.txt'
        response['preview'] = render_template(tmpl_file, order=order_data)

    return jsonify(response)


@api_blueprint.route('/<order_pid>/send_order', methods=['POST'])
@check_logged_as_librarian
@jsonify_error
def send_order(order_pid):
    """HTTP POST for sending an acquisition order.

    Required parameters:
        order_pid: the pid of the order.
        emails: the list of recipients (a list of dictionaries each contains
        the email and its type to, cc, reply_to, or bcc).
    """
    order = AcqOrder.get_record_by_pid(order_pid)
    if not order:
        abort(404, "Acquisition order not found")

    data = flask_request.get_json()
    emails = data.get('emails')
    if not emails:
        abort(400, "Missing recipients emails.")
    notifications = order.send_order(emails=emails)
    response = {'data': notifications}
    return jsonify(response)
