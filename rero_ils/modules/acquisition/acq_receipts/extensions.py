# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Acquisition Receipt record extensions."""

from invenio_records.extensions import RecordExtension


class AcqReceiptExtension(RecordExtension):
    """Defines hooks about API functions calls for AcqReceipt."""

    def pre_delete(self, record, force=False):
        """Called before a record is deleted.

        :param record: the record metadata.
        :param force: force the deleting of the record.
        """
        # For receipts, we are allowed to delete all of its receipt lines
        # without further checks.
        for line in record.get_receipt_lines():
            line.delete(force=force, delindex=True)


class AcquisitionReceiptCompleteDataExtension(RecordExtension):
    """Complete data about an acquisition receipt."""

    def post_create(self, record):
        """Called after the record is created.

        If no reference is provided, use the PID as auto incremented sequence
        to use as reference order.

        :param record: the record metadata.
        """
        if not record.get('reference'):
            record['reference'] = f'RECEIPT-{record.pid}'
            record.update(record, dbcommit=True, reindex=True)
