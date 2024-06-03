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

"""Acquisition receipt lines JSON schema tests."""

from __future__ import absolute_import, print_function

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
