# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition orders JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.acquisition.acq_orders.api import AcqOrder
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderNoteType


def test_notes(app, acq_order_schema, acq_order_fiction_martigny_data_tmp):
    """Test notes acq orders jsonschemas."""

    order_data = acq_order_fiction_martigny_data_tmp
    order_data["notes"] = [
        {"type": AcqOrderNoteType.STAFF, "content": "note content"},
        {"type": AcqOrderNoteType.VENDOR, "content": "note content 2"},
    ]
    validate(order_data, acq_order_schema)

    with pytest.raises(ValidationError):
        order_data["notes"] = [
            {"type": AcqOrderNoteType.STAFF, "content": "note content"},
            {"type": AcqOrderNoteType.STAFF, "content": "note content 2"},
        ]
        AcqOrder.validate(AcqOrder(order_data))
