# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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
