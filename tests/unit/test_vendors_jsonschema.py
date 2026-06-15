# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Vendors JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.vendors.api import Vendor


def test_vendors_special_rero_validation(app, vendor_martigny_data, vendors_schema):
    """Test RERO special validation data"""
    record = copy.deepcopy(vendor_martigny_data)
    validate(record, vendors_schema)

    record["contacts"].append(record["contacts"][0])
    with pytest.raises(ValidationError) as err:
        Vendor.validate(Vendor(record))
    assert "Cannot have multiple contacts with the same type" in str(err)

    record["contacts"] = vendor_martigny_data["contacts"]
    record["notes"].append(record["notes"][0])
    with pytest.raises(ValidationError) as err:
        Vendor.validate(Vendor(record))
    assert "Cannot have multiple notes with the same type" in str(err)
