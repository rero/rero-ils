# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Vendors JSON schema tests."""

from __future__ import absolute_import, print_function

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.vendors.api import Vendor


def test_vendors_special_rero_validation(
    app, vendor_martigny_data, vendors_schema
):
    """Test RERO special validation data"""
    record = copy.deepcopy(vendor_martigny_data)
    validate(record, vendors_schema)

    record['contacts'].append(record['contacts'][0])
    with pytest.raises(ValidationError) as err:
        Vendor.validate(Vendor(record))
    assert 'Can not have multiple contacts with the same type' in str(err)

    record['contacts'] = vendor_martigny_data['contacts']
    record['notes'].append(record['notes'][0])
    with pytest.raises(ValidationError) as err:
        Vendor.validate(Vendor(record))
    assert 'Can not have multiple notes with the same type' in str(err)
