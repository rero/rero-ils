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

"""Item utils."""

from flask import jsonify
from flask_babelex import gettext as _

from .api import Item, ItemStatus
from ..libraries.api import Library
from ..loans.api import Loan
from ..loans.utils import can_be_requested
from ..patrons.api import Patron


def jsonify_response(response=False, reason=None):
    """Jsonify api response."""
    return jsonify({
        'can_request': response,
        'reason': reason
    })


def is_librarian_can_request_item_for_patron(
        item_pid, library_pid, patron_barcode):
    """Check if a librarian can request an item for a patron.

    required_parameters: item_pid, library_pid, patron_barcode
    """
    item = Item.get_record_by_pid(item_pid)
    if not item:
        return jsonify_response(reason=_('Item not found.'))
    patron = Patron.get_patron_by_barcode(patron_barcode)
    if not patron:
        return jsonify_response(reason=_('Patron not found.'))
    library = Library.get_record_by_pid(library_pid)
    if not library:
        return jsonify_response(reason=_('Library not found.'))
    # Create a loan
    loan = Loan({
        'patron_pid': patron.pid, 'item_pid': item.pid,
        'library_pid': library_pid})
    if not can_be_requested(loan):
        return jsonify_response(
            reason=_(
                'Circulation policies do not allow request on this item.'))
    if item.status != ItemStatus.MISSING:
        loaned_to_patron = item.is_loaned_to_patron(patron_barcode)
        if loaned_to_patron:
            return jsonify_response(
                reason=_(
                    'Item is already checked-out or requested by patron.'))
        return jsonify_response(
            response=True, reason=_('Request is possible.'))
    else:
        return jsonify_response(
            reason=_('Item status does not allow requests.'))
