# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

from flask import Blueprint, abort, jsonify

from rero_ils.modules.acq_orders.api import AcqOrder
from rero_ils.modules.acq_orders.dumpers import AcqOrderNotificationDumper
from rero_ils.modules.decorators import check_logged_as_librarian

api_blueprint = Blueprint(
    'api_order',
    __name__,
    url_prefix='/acq_order'
)


@api_blueprint.route('/<order_pid>/acquisition_order/preview', methods=['GET'])
@check_logged_as_librarian
def order_notification_preview(order_pid):
    """Get the preview of an acquisition order notification content."""
    order = AcqOrder.get_record_by_pid(order_pid)
    if not order:
        abort(404)

    return jsonify({
        'data': order.dumps(dumper=AcqOrderNotificationDumper()),
    })
