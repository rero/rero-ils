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

"""Utils functions about acquisition account."""
from rero_ils.modules.notifications.models import RecipientType
from rero_ils.modules.patrons.api import current_librarian


def get_history(order):
    """Find the acquisition order history.

    :param order: the source acquisition order.
    :return a sorted list of order representing the order history.
    """
    history = [order]
    current_order = order
    while prev_order := current_order.previous_order:
        history[:0] = [prev_order]
        current_order = prev_order
    current_order = order
    while next_order := current_order.next_order:
        history.append(next_order)
        current_order = next_order
    return history


def get_recipient_suggestions(order):
    """Get the recipient email suggestions for an order.

    :param order: the acquisition order to analyze.
    :return: the list of suggested emails.
    :rtype list<{type: list<str>, address: str}>
    """
    # Build suggestions email :
    #   1) related vendor order email (default TO recipient type)
    #   2) related library acquisition settings information
    #   3) current logged user
    suggestions = {}
    if (vendor := order.vendor) and (email := vendor.order_email):
        suggestions.setdefault(email, set()).update([RecipientType.TO])
    if settings := (order.library or {}).get('acquisition_settings'):
        if email := settings.get('shipping_informations', {}).get('email'):
            suggestions.setdefault(email, set())\
                .update([RecipientType.CC, RecipientType.REPLY_TO])
        if email := settings.get('billing_informations', {}).get('email'):
            suggestions.setdefault(email, set())
    if email := current_librarian.user.email:
        suggestions.setdefault(email, set())

    # sometimes, the recipient types could be an empty set. In this case, we
    # don't need to return this key --> clean the build suggestions dict and
    # return a recipient suggestion array.
    cleaned_suggestions = []
    for recipient_address, recipient_types in suggestions.items():
        suggestion = {'address': recipient_address}
        if recipient_types:
            suggestion['type'] = list(recipient_types)
        cleaned_suggestions.append(suggestion)
    return cleaned_suggestions
