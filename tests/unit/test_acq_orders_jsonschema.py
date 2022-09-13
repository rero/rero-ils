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

"""Acquisition orders JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.acquisition.acq_orders.api import AcqOrder
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderNoteType


def test_notes(app, acq_order_schema, acq_order_fiction_martigny_data_tmp):
    """Test notes acq orders jsonschemas."""

    order_data = acq_order_fiction_martigny_data_tmp
    order_data['notes'] = [
        {'type': AcqOrderNoteType.STAFF, 'content': 'note content'},
        {'type': AcqOrderNoteType.VENDOR, 'content': 'note content 2'},
    ]
    validate(order_data, acq_order_schema)

    with pytest.raises(ValidationError):
        order_data['notes'] = [
            {'type': AcqOrderNoteType.STAFF, 'content': 'note content'},
            {'type': AcqOrderNoteType.STAFF, 'content': 'note content 2'},
        ]
        AcqOrder.validate(AcqOrder(order_data))
