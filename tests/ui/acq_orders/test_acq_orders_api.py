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

from rero_ils.modules.acq_order_lines.models import AcqOrderLineStatus
from rero_ils.modules.acq_orders.models import AcqOrderNoteType, AcqOrderStatus


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
    assert acol1['status'] == acol2['status'] == AcqOrderLineStatus.APPROVED
    assert acor.status == AcqOrderStatus.PENDING

    acol2['status'] = AcqOrderLineStatus.RECEIVED
    acol2.update(acol2, dbcommit=True, reindex=True)
    assert acor.status == AcqOrderStatus.PARTIALLY_RECEIVED

    acol1['status'] = AcqOrderLineStatus.RECEIVED
    acol1.update(acol1, dbcommit=True, reindex=True)
    assert acor.status == AcqOrderStatus.RECEIVED

    # ORDER LINES -------------------------------------------------------------
    assert len(list(acor.get_order_lines())) == \
        acor.get_order_lines(output='count')

    # TOTAL AMOUNT ------------------------------------------------------------
    total_amount = acol1.get('total_amount') + acol2.get('total_amount')
    assert acor.get_order_total_amount() == total_amount
    acol1['status'] = AcqOrderLineStatus.CANCELLED
    acol1.update(acol1, dbcommit=True, reindex=True)
    assert acor.get_order_total_amount() == acol2.get('total_amount')

    # RESET CHANGES
    acol1['status'] = AcqOrderLineStatus.APPROVED
    acol1.update(acol1, dbcommit=True, reindex=True)

    # ORDER DATE --------------------------------------------------------------
    assert acor.order_date is None

    acol2['status'] = AcqOrderLineStatus.ORDERED
    acol2['order_date'] = yesterday.strftime('%Y-%m-%d')
    acol2.update(acol2, dbcommit=True, reindex=True)
    assert acor.order_date == yesterday.strftime('%Y-%m-%d')

    # reset changes
    acol2['status'] = AcqOrderLineStatus.APPROVED
    del acol2['order_date']
    acol2.update(acol2, dbcommit=True, reindex=True)

    # ORDER NOTE --------------------------------------------------------------
    note_content = 'test note content'
    assert acor.get_note(AcqOrderNoteType.VENDOR) is None
    acor.setdefault('notes', []).append({
        'type': AcqOrderNoteType.VENDOR,
        'content': note_content
    })
    assert acor.get_note(AcqOrderNoteType.VENDOR) == note_content
    del acor['notes']
