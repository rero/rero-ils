# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition order lines API tests."""

from copy import deepcopy
from unittest import mock

import pytest
from jsonschema import ValidationError

from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.utils import get_ref_for_pid


def test_build_total_amount():
    """Total amount is amount * quantity, rounded to 2 decimal places."""
    data = {"amount": 10.50, "quantity": 3}
    AcqOrderLine._build_total_amount(data)
    assert data["total_amount"] == 31.50

    # Float drift: 0.1 * 3 in Python = 0.30000000000000004 without round
    data = {"amount": 0.10, "quantity": 3}
    AcqOrderLine._build_total_amount(data)
    assert data["total_amount"] == 0.30


def test_order_line_properties(
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_account_fiction_martigny,
    document,
):
    """Test order line properties."""
    order_line = acq_order_line_fiction_martigny
    assert order_line.account.pid == acq_account_fiction_martigny.pid
    assert order_line.order_pid == acq_order_fiction_martigny.pid
    assert order_line.order.pid == acq_order_fiction_martigny.pid
    assert order_line.document.pid == document.pid
    assert order_line.unreceived_quantity == order_line.get("quantity")


def test_order_line_validation_extension(acq_order_line_fiction_martigny_data, acq_account_fiction_martigny, ebook_1):
    """Test order line validation extension."""
    data = deepcopy(acq_order_line_fiction_martigny_data)
    del data["pid"]

    # An order line cannot be linked to an harvested document
    ebook_ref = get_ref_for_pid("doc", ebook_1.pid)
    test_data = deepcopy(data)
    test_data["document"]["$ref"] = ebook_ref
    with pytest.raises(ValidationError) as error:
        AcqOrderLine.create(test_data, delete_pid=True)
    assert "Cannot link to an harvested document" in str(error.value)


def test_order_line_cancel_on_received_order(acq_order_line_fiction_martigny):
    """Test cancelling a line is valid even when the order became received."""
    order_line = acq_order_line_fiction_martigny
    with mock.patch(
        "rero_ils.modules.acquisition.acq_orders.api.AcqOrder.get_status_by_pid",
        mock.MagicMock(return_value=AcqOrderStatus.RECEIVED),
    ):
        order_line["is_cancelled"] = True
        assert order_line.extended_validation() is True

        # a non-cancelling update on a received order is still rejected
        order_line["is_cancelled"] = False
        assert isinstance(order_line.extended_validation(), str)
