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

"""Acquisition receipt record mapping tests."""
from utils import get_mapping

from rero_ils.modules.acq_receipts.api import AcqReceipt, AcqReceiptsSearch


def test_acq_receipts_es_mapping(es, db, lib_martigny, vendor_martigny,
                                 acq_order_fiction_martigny,
                                 acq_receipt_fiction_martigny_data):
    """Test acquisition receipts elasticsearch mapping."""
    search = AcqReceiptsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    receipt = AcqReceipt.create(
        acq_receipt_fiction_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
    receipt.delete(force=True, dbcommit=True, delindex=True)
