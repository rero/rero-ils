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

"""Define relation between records and buckets."""


class LoanState:
    """Class to handle different loan states."""

    CREATED = 'CREATED'
    PENDING = 'PENDING'
    ITEM_IN_TRANSIT_FOR_PICKUP = 'ITEM_IN_TRANSIT_FOR_PICKUP'
    ITEM_IN_TRANSIT_TO_HOUSE = 'ITEM_IN_TRANSIT_TO_HOUSE'
    ITEM_AT_DESK = 'ITEM_AT_DESK'
    ITEM_ON_LOAN = 'ITEM_ON_LOAN'
    ITEM_RETURNED = 'ITEM_RETURNED'
    CANCELLED = 'CANCELLED'

    CONCLUDED = [CANCELLED, ITEM_RETURNED]
    ITEM_IN_TRANSIT = [ITEM_IN_TRANSIT_TO_HOUSE, ITEM_IN_TRANSIT_FOR_PICKUP]
    REQUEST_STATES = [PENDING, ITEM_AT_DESK, ITEM_IN_TRANSIT_FOR_PICKUP]


class LoanAction:
    """Class holding all available circulation loan actions."""

    REQUEST = 'request'
    CHECKOUT = 'checkout'
    CHECKIN = 'checkin'
    VALIDATE = 'validate'
    RECEIVE = 'receive'
    RETURN_MISSING = 'return_missing'
    EXTEND = 'extend_loan'
    CANCEL = 'cancel'
    NO = 'no'
    UPDATE = 'update'
