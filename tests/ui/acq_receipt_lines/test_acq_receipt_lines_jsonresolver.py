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

"""Acq receipt line JSONResolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError

from rero_ils.modules.utils import extracted_data_from_ref


def test_acq_receipt_lines_jsonresolver(acq_receipt_line_1_fiction_martigny):
    """Acquisition receipt lines resolver tests."""
    data = {'$ref': 'https://bib.rero.ch/api/acq_receipt_lines/acrl1'}
    rec = Record.create({'acq_receipt_line': data})
    assert extracted_data_from_ref(rec.get('acq_receipt_line')) == 'acrl1'
    # deleted record
    acq_receipt_line_1_fiction_martigny.delete()
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()

    # non existing record
    data = {'$ref': 'https://bib.rero.ch/api/acq_receipt_lines/n_e'}
    rec = Record.create({'acq_receipt_line': data})
    with pytest.raises(JsonRefError):
        type(rec)(rec.replace_refs()).dumps()
