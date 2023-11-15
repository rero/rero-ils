# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Acq order line JSONResolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError

from rero_ils.modules.utils import extracted_data_from_ref


def test_acq_order_lines_jsonresolver(
        document, acq_order_line_fiction_martigny):
    """Acquisition order lines resolver tests."""
    rec = Record.create({
        'acq_order_line': {
            '$ref': 'https://bib.rero.ch/api/acq_order_lines/acol1'
        }
    })
    assert extracted_data_from_ref(rec.get('acq_order_line')) == 'acol1'
    # deleted record
    acq_order_line_fiction_martigny.delete()
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()

    # non existing record
    rec = Record.create({
        'acq_order_line': {
            '$ref': 'https://bib.rero.ch/api/acq_order_lines/n_e'
        }
    })
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()
