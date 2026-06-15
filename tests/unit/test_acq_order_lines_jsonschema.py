# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition order lines JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.acquisition.acq_order_lines.models import AcqOrderLineNoteType


def test_notes(app, acq_order_line_schema, acq_order_line_fiction_martigny_data_tmp):
    """Test notes acq order lines jsonschemas."""

    order_line_data = acq_order_line_fiction_martigny_data_tmp
    order_line_data["notes"] = [
        {"type": AcqOrderLineNoteType.STAFF, "content": "note content"},
        {"type": AcqOrderLineNoteType.VENDOR, "content": "note content 2"},
    ]
    validate(order_line_data, acq_order_line_schema)

    with pytest.raises(ValidationError):
        order_line_data["notes"] = [
            {"type": AcqOrderLineNoteType.STAFF, "content": "note content"},
            {"type": AcqOrderLineNoteType.STAFF, "content": "note content 2"},
        ]
        AcqOrderLine.validate(AcqOrderLine(order_line_data))
