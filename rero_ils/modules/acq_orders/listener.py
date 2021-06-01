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

"""Signals connector for acquisition order."""


from .api import AcqOrdersSearch


def enrich_acq_order_data(sender, json=None, record=None, index=None,
                          doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The document type of the record.
    """
    if index.split('-')[0] == AcqOrdersSearch.Meta.index:
        # for each related order lines : add some informations
        json['order_lines'] = []
        for order_line in record.get_order_lines():
            json['order_lines'].append(order_line.dump_for_order())
        # other dynamic keys
        json['organisation'] = {
            'pid': record.organisation_pid,
            'type': 'org',
        }
        json['status'] = record.status
