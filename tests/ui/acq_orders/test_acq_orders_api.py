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
from rero_ils.modules.acq_orders.models import AcqOrderStatus


def test_order_status(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny
):
    """Test order status."""
    acol1 = acq_order_line_fiction_martigny
    acol2 = acq_order_line2_fiction_martigny
    acor = acq_order_fiction_martigny
    assert acol1['status'] == acol2['status'] == AcqOrderLineStatus.APPROVED
    assert acor.status == AcqOrderStatus.PENDING

    acol2['status'] = AcqOrderLineStatus.RECEIVED
    acol2.update(acol2, dbcommit=True, reindex=True)
    assert acor.status == AcqOrderStatus.PARTIALLY_RECEIVED

    acol1['status'] = AcqOrderLineStatus.RECEIVED
    acol1.update(acol1, dbcommit=True, reindex=True)
    assert acor.status == AcqOrderStatus.RECEIVED

    # RESET
    acol1['status'] = AcqOrderLineStatus.APPROVED
    acol1.update(acol1, dbcommit=True, reindex=True)
    acol1['status'] = AcqOrderLineStatus.APPROVED
    acol1.update(acol1, dbcommit=True, reindex=True)


def test_order_get_order_lines(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny
):
    """Test order get_order_lines."""
    acor = acq_order_fiction_martigny
    assert len(list(acor.get_order_lines())) == \
        acor.get_order_lines(count=True)
