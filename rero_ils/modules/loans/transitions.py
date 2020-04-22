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

"""REROILS Circulation custom transitions."""


from invenio_circulation.api import get_document_pid_by_item_pid, \
    get_pending_loans_by_doc_pid
from invenio_circulation.proxies import current_circulation
from invenio_circulation.transitions.base import Transition
from invenio_circulation.transitions.transitions import \
    _ensure_same_location as _ensure_same_location
from invenio_circulation.transitions.transitions import ensure_same_item
from invenio_db import db

from ..documents.api import Document


def _update_document_pending_request_for_item(item_pid, **kwargs):
    """Update pending loans on a Document with no Item attached yet.

    :param item_pid: a dict containing `value` and `type` fields to
        uniquely identify the item.
    """
    document_pid = get_document_pid_by_item_pid(item_pid)
    document = Document.get_record_by_pid(document_pid)
    if document.get_number_of_items() == 1:
        for pending_loan in get_pending_loans_by_doc_pid(document_pid):
            pending_loan['item_pid'] = item_pid
            pending_loan.commit()
            db.session.commit()
            current_circulation.loan_indexer().index(pending_loan)


class ItemInTransitHouseToItemReturned(Transition):
    """Check-in action when returning an item to its belonging location."""

    def __init__(
        self, src, dest, trigger="next", permission_factory=None, **kwargs
    ):
        """Constructor."""
        super().__init__(
            src,
            dest,
            trigger=trigger,
            permission_factory=permission_factory,
            **kwargs
        )
        self.assign_item = kwargs.get("assign_item", True)

    @ensure_same_item
    def before(self, loan, **kwargs):
        """Validate check-in action."""
        super().before(loan, **kwargs)

        _ensure_same_location(
            loan['item_pid'],
            loan['transaction_location_pid'],
            self.dest,
            error_msg="Item should be in transit to house.",
        )

    def after(self, loan):
        """Check for pending requests on this item after check-in."""
        super().after(loan)
        if self.assign_item:
            _update_document_pending_request_for_item(loan['item_pid'])


class ItemOnLoanToItemReturned(Transition):
    """Check-in action when returning an item to its belonging location."""

    def __init__(
        self, src, dest, trigger="next", permission_factory=None, **kwargs
    ):
        """Constructor."""
        super().__init__(
            src,
            dest,
            trigger=trigger,
            permission_factory=permission_factory,
            **kwargs
        )
        self.assign_item = kwargs.get("assign_item", True)

    @ensure_same_item
    def before(self, loan, **kwargs):
        """Validate check-in action."""
        super().before(loan, **kwargs)

        _ensure_same_location(
            loan['item_pid'],
            loan['transaction_location_pid'],
            self.dest,
            error_msg="Item should be in transit to house.",
        )

        # set end loan date as transaction date when completing loan
        loan['end_date'] = loan['transaction_date']

    def after(self, loan):
        """Check for pending requests on this item after check-in."""
        super().after(loan)
        if self.assign_item:
            _update_document_pending_request_for_item(loan['item_pid'])
