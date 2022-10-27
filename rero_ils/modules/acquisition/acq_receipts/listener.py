# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Signals connector for acquisition receipt."""

from rero_ils.modules.acquisition.acq_receipt_lines.dumpers import \
    AcqReceiptLineESDumper

from .api import AcqReceiptsSearch


def enrich_acq_receipt_data(sender, json=None, record=None, index=None,
                            doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The document type of the record.
    """
    if index.split('-')[0] == AcqReceiptsSearch.Meta.index:
        # add related order lines metadata
        json['receipt_lines'] = [
            receipt_line.dumps(dumper=AcqReceiptLineESDumper())
            for receipt_line in record.get_receipt_lines()
        ]
        # other dynamic keys
        json['total_amount'] = record.total_amount
        json['quantity'] = record.total_item_quantity
