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

"""Acquisition invoice record mapping tests."""
from utils import get_mapping

from rero_ils.modules.acquisition.acq_invoices.api import (
    AcquisitionInvoice,
    AcquisitionInvoicesSearch,
)


def test_acq_invoices_es_mapping(
    es,
    db,
    lib_martigny,
    vendor_martigny,
    acq_invoice_fiction_martigny_data,
    document,
    document_ref,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
):
    """Test acquisition account elasticsearch mapping."""
    search = AcquisitionInvoicesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    invoice = AcquisitionInvoice.create(
        acq_invoice_fiction_martigny_data, dbcommit=True, reindex=True, delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
    invoice.delete(force=True, dbcommit=True, delindex=True)
