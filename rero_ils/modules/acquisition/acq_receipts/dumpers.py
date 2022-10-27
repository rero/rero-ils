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

"""Acquisition receipt dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class AcqReceiptESDumper(InvenioRecordsDumper):
    """ElasticSearch dumper class for an AcqReceipt."""

    def dump(self, record, data):
        """Dump an AcqReceipt instance for ElasticSearch.

        For ElasticSearch integration, we need to dump basic informations from
        a `AcqReceipt` object instance, and add receipt date from related
        `AcqReceptionLine`.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        metadata = {
            'pid': record.pid,
            'reference': record.get('reference'),
            'receipt_date': list(set([
                line.get('receipt_date') for line in record.get_receipt_lines()
            ]))
        }
        metadata = {k: v for k, v in metadata.items() if v}
        data.update(metadata)
        return data
