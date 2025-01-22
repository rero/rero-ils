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

"""Acquisition orders API tests."""

from rero_ils.modules.acquisition.acq_order_lines.models import (
    AcqOrderLineNoteType,
    AcqOrderLineStatus,
)
from rero_ils.modules.acquisition.acq_orders.api import AcqOrdersSearch
from rero_ils.modules.acquisition.acq_orders.models import (
    AcqOrderNoteType,
    AcqOrderStatus,
)
from rero_ils.modules.utils import get_ref_for_pid


def test_order_properties(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
    yesterday,
):
    """Test order properties."""
    acol1 = acq_order_line_fiction_martigny
    acol2 = acq_order_line2_fiction_martigny
    acor = acq_order_fiction_martigny

    # STATUS ------------------------------------------------------------------
    assert acol1.status == acol2.status == AcqOrderLineStatus.APPROVED
    assert acor.status == AcqOrderStatus.PENDING

    # ORDER LINES -------------------------------------------------------------
    assert len(list(acor.get_order_lines())) == acor.get_order_lines(output="count")

    # TOTAL AMOUNT ------------------------------------------------------------
    total_amount = acol1.get("total_amount") + acol2.get("total_amount")
    assert acor.get_order_provisional_total_amount() == total_amount
    acol1["is_cancelled"] = True
    acol1.update(acol1, dbcommit=True, reindex=True)
    assert acor.get_order_provisional_total_amount() == acol2.get("total_amount")

    # RESET CHANGES
    acol1["is_cancelled"] = False
    acol1.update(acol1, dbcommit=True, reindex=True)

    # NOTES -------------------------------------------------------------------
    note_content = "test note content"
    assert acor.get_note(AcqOrderNoteType.VENDOR) is None
    acor.setdefault("notes", []).append(
        {"type": AcqOrderNoteType.VENDOR, "content": note_content}
    )
    assert acor.get_note(AcqOrderNoteType.VENDOR) == note_content
    del acor["notes"]

    # Check that `related notes` content return the note from `acol1`
    assert any(
        note[0]["type"] == AcqOrderLineNoteType.STAFF
        and note[1] == acol1.__class__
        and note[2] == acol1.pid
        for note in acor.get_related_notes()
    )

    # ORDER ITEM QUANTITY -----------------------------------------------------
    assert acor.item_quantity == 6
    assert acor.item_received_quantity == 0


def test_get_related_orders(acq_order_fiction_martigny, acq_order_fiction_saxon):
    """Test relations between acquisition order."""
    acor_martigny = acq_order_fiction_martigny
    acor_saxon = acq_order_fiction_saxon
    acor_saxon["previousVersion"] = {"$ref": get_ref_for_pid("acor", acor_martigny.pid)}
    # remove dynamic loaded key
    acor_saxon.pop("account_statement", None)
    acor_saxon.pop("status", None)
    acor_saxon.pop("order_date", None)
    acor_saxon = acor_saxon.update(acor_saxon, dbcommit=True, reindex=True)
    AcqOrdersSearch.flush_and_refresh()

    related_acors = list(acor_martigny.get_related_orders())
    assert related_acors == [acor_saxon]
    assert acor_martigny.get_related_orders(output="count") == 1
    assert acor_martigny.get_links_to_me(True)["orders"] == [acor_saxon.pid]
