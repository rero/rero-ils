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

"""Acquisition order lines API tests."""


def test_order_line_properties(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_account_fiction_martigny,
    document
):
    """Test order line properties."""
    assert acq_order_line_fiction_martigny.account.pid ==\
        acq_account_fiction_martigny.pid
    assert acq_order_line_fiction_martigny.order.pid == \
        acq_order_fiction_martigny.pid
    assert acq_order_line_fiction_martigny.document.pid == document.pid
