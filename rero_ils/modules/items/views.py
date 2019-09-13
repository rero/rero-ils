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

from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, \
    render_template, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from .api import Item
from .models import ItemStatus
from ..documents.api import Document
from ..item_types.api import ItemType
from ..libraries.api import Library
from ..locations.api import Location
from ...filter import format_date_filter
from ...permissions import request_item_permission


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
    document = Document.get_record_by_pid(
        record.replace_refs()['document']['pid'])
    item = record.replace_refs()
    location = Location.get_record_by_pid(item['location']['pid'])
    library = Library.get_record_by_pid(
        location.replace_refs()['library']['pid'])
    item_type = ItemType.get_record_by_pid(item['item_type']['pid'])
    return render_template(
        template, pid=pid, record=record, document=document, location=location,
        library=library, item_type=item_type, viewcode=kwargs['viewcode'])


blueprint = Blueprint(
    'item',
    __name__,
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


def jsonify_error(func):
    """Jsonify the errors."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({'status': 'error: {error}'.format(error=e)}), 500
    return decorated_view


@blueprint.route(
    '/<string:viewcode>/item/request/<item_pid>/<pickup_location_pid>',
    methods=['GET'])
@check_authentication_for_request
@jsonify_error
def patron_request(viewcode, item_pid=None, pickup_location_pid=None):
    """HTTP GET request for Item request action...

    required_parameters: item_pid_value, location
    """
    data = {
        'item_pid': item_pid,
        'pickup_location_pid': pickup_location_pid
    }
    item = Item.get_record_by_pid(data.get('item_pid'))

    item_data, action_applied = item.request(
        **data
    )
    flash(_('The item %s has been requested.' % item_pid), 'success')
    document_pid = item.replace_refs().get('document', {}).get('pid')
    return redirect(url_for(
        'invenio_records_ui.doc',
        viewcode=viewcode,
        pid_value=document_pid
    ))


@blueprint.app_template_filter()
def not_available_reasons(item):
    """Returns reasons why item is not available."""
    text = ''
    if not item.available:
        if item.status == ItemStatus.ON_LOAN:
            due_date = format_date_filter(
                item.get_item_end_date(),
                format='short_date',
                locale='en')
            text = '{msg} {date}'.format(
                msg=_('due until'),
                date=due_date)
        elif item.status == ItemStatus.IN_TRANSIT:
            text = '{msg}'.format(
                msg=_('in transit'))

        if item.number_of_requests():
            text += ' ({number} {msg})'.format(
                number=item.number_of_requests(),
                msg=_('requests'))
    return text.strip()
