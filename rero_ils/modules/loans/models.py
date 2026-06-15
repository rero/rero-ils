# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""


class LoanState:
    """Class to handle different loan states."""

    CREATED = "CREATED"
    PENDING = "PENDING"
    ITEM_IN_TRANSIT_FOR_PICKUP = "ITEM_IN_TRANSIT_FOR_PICKUP"
    ITEM_IN_TRANSIT_TO_HOUSE = "ITEM_IN_TRANSIT_TO_HOUSE"
    ITEM_AT_DESK = "ITEM_AT_DESK"
    ITEM_ON_LOAN = "ITEM_ON_LOAN"
    ITEM_RETURNED = "ITEM_RETURNED"
    CANCELLED = "CANCELLED"

    CONCLUDED = [CANCELLED, ITEM_RETURNED]
    ITEM_IN_TRANSIT = [ITEM_IN_TRANSIT_TO_HOUSE, ITEM_IN_TRANSIT_FOR_PICKUP]
    REQUEST_STATES = [PENDING, ITEM_AT_DESK, ITEM_IN_TRANSIT_FOR_PICKUP]


class LoanAction:
    """Class holding all available circulation loan actions."""

    REQUEST = "request"
    CHECKOUT = "checkout"
    CHECKIN = "checkin"
    VALIDATE = "validate"
    RECEIVE = "receive"
    RETURN_MISSING = "return_missing"
    EXTEND = "extend_loan"
    CANCEL = "cancel"
    NO = "no"
    UPDATE = "update"
