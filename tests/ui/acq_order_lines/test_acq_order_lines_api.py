# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition order lines API tests."""

from copy import deepcopy

import pytest
from jsonschema import ValidationError

from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.utils import get_ref_for_pid


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
