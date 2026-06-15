# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipt lines JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_vat_rate(acq_receipt_line_1_fiction_martigny, acq_receipt_line_schema):
    """Test VAT rate for acq receipt lines jsonschemas."""

    receipt_line_data = acq_receipt_line_1_fiction_martigny
    validate(receipt_line_data, acq_receipt_line_schema)

    with pytest.raises(ValidationError):
        receipt_line_data["vat_rate"] = -1
        validate(receipt_line_data, acq_receipt_line_schema)

    with pytest.raises(ValidationError):
        receipt_line_data["vat_rate"] = 101
        validate(receipt_line_data, acq_receipt_line_schema)
