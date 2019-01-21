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

from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, \
    render_template, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from ...permissions import request_item_permission
from ..documents.api import Document
from ..item_types.api import ItemType
from ..libraries.api import Library
from ..locations.api import Location
from .api import Item


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
        library=library, item_type=item_type)


blueprint = Blueprint(
    'item',
    __name__,
    url_prefix='/item',
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
    """."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise(e)
            return jsonify({'status': 'error: {error}'.format(error=e)}), 500
    return decorated_view


@blueprint.route('/request/<item_pid>/<pickup_location_pid>',
                 methods=['GET'])
@check_authentication_for_request
@jsonify_error
def patron_request(item_pid=None, pickup_location_pid=None):
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
    return redirect(
        url_for("invenio_records_ui.doc", pid_value=document_pid))
