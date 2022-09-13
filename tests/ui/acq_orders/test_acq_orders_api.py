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

from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineNoteType, AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderNoteType, \
    AcqOrderStatus


def test_order_properties(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
    yesterday
):
    """Test order properties."""
    acol1 = acq_order_line_fiction_martigny
    acol2 = acq_order_line2_fiction_martigny
    acor = acq_order_fiction_martigny

    # STATUS ------------------------------------------------------------------
    assert acol1.status == acol2.status == AcqOrderLineStatus.APPROVED
    assert acor.status == AcqOrderStatus.PENDING

    # ORDER LINES -------------------------------------------------------------
    assert len(list(acor.get_order_lines())) == \
        acor.get_order_lines(output='count')

    # TOTAL AMOUNT ------------------------------------------------------------
    total_amount = acol1.get('total_amount') + acol2.get('total_amount')
    assert acor.get_order_provisional_total_amount() == total_amount
    acol1['is_cancelled'] = True
    acol1.update(acol1, dbcommit=True, reindex=True)
    assert acor.get_order_provisional_total_amount() == \
           acol2.get('total_amount')

    # RESET CHANGES
    acol1['is_cancelled'] = False
    acol1.update(acol1, dbcommit=True, reindex=True)

    # ORDER DATE --------------------------------------------------------------
    assert acor.order_date is None

    acol2['order_date'] = yesterday.strftime('%Y-%m-%d')
    acol2.update(acol2, dbcommit=True, reindex=True)
    assert acor.order_date == yesterday.strftime('%Y-%m-%d')
    assert acor.status == AcqOrderStatus.ORDERED

    # reset changes
    del acol2['order_date']
    acol2.update(acol2, dbcommit=True, reindex=True)

    # NOTES -------------------------------------------------------------------
    note_content = 'test note content'
    assert acor.get_note(AcqOrderNoteType.VENDOR) is None
    acor.setdefault('notes', []).append({
        'type': AcqOrderNoteType.VENDOR,
        'content': note_content
    })
    assert acor.get_note(AcqOrderNoteType.VENDOR) == note_content
    del acor['notes']

    # Check that `related notes` content return the note from `acol1`
    assert any(
        note[0]['type'] == AcqOrderLineNoteType.STAFF
        and note[1] == acol1.__class__
        and note[2] == acol1.pid
        for note in acor.get_related_notes()
    )

    # ORDER ITEM QUANTITY -----------------------------------------------------
    assert acor.item_quantity == 6
    assert acor.item_received_quantity == 0
