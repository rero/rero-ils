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

"""Signals connector for acquisition order line."""
from rero_ils.modules.acq_invoices.api import AcquisitionInvoicesSearch
from rero_ils.modules.acq_order_lines.api import AcqOrderLine, \
    AcqOrderLinesSearch


def enrich_acq_order_line_data(sender, json=None, record=None, index=None,
                               doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The document type of the record.
    """
    if index.split('-')[0] == AcqOrderLinesSearch.Meta.index:
        order_line = record
        if not isinstance(record, AcqOrderLine):
            order_line = AcqOrderLine.get_record_by_pid(record.get('pid'))

        # Link to invoice
        #   To compute account encumbrance/expenditure, we need to know if the
        #   order line is already linked to an invoice.
        es_query = AcquisitionInvoicesSearch()\
            .filter('term', invoice_items__acq_order_line__pid=order_line.pid)\
            .source(['pid']).scan()
        _exhausted = object()
        hit = next(es_query, _exhausted)
        if hit != _exhausted:
            json['acq_invoice'] = dict(pid=hit.pid, type='acin')
