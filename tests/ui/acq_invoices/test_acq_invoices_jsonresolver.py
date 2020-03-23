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

"""Acq order JSONResolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError


def test_acq_invoices_jsonresolver(acq_invoice_fiction_martigny):
    """Acquisition invoices resolver tests."""
    rec = Record.create({
        'acq_invoice': {'$ref': 'https://ils.rero.ch/api/acq_invoices/acin1'}
    })
    assert rec.replace_refs().get('acq_invoice') == {'pid': 'acin1'}
    # deleted record
    acq_invoice_fiction_martigny.delete()
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()

    # non existing record
    rec = Record.create({
        'acq_invoice': {'$ref': 'https://ils.rero.ch/api/acq_invoices/n_e'}
    })
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()
