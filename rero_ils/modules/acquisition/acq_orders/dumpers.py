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

"""Acquisition order dumpers."""
from datetime import date

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.acquisition.acq_order_lines.dumpers import \
    AcqOrderLineNotificationDumper
from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderNoteType
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.libraries.dumpers import \
    LibraryAcquisitionNotificationDumper
from rero_ils.modules.vendors.api import Vendor
from rero_ils.modules.vendors.dumpers import \
    VendorAcquisitionNotificationDumper


class AcqOrderNotificationDumper(InvenioRecordsDumper):
    """Order dumper class for acquisition order notification."""

    def dump(self, record, data):
        """Dump an AcqOrder instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        today = date.today().strftime('%Y-%m-%d')
        data.update({
            'reference': record.get('reference'),
            'order_date': record.order_date or today,
            'note': record.get_note(AcqOrderNoteType.VENDOR),
        })
        library = Library.get_record_by_pid(record.library_pid)
        data['library'] = library.dumps(
            dumper=LibraryAcquisitionNotificationDumper())
        vendor = Vendor.get_record_by_pid(record.vendor_pid)
        data['vendor'] = vendor.dumps(
            dumper=VendorAcquisitionNotificationDumper())
        data['order_lines'] = [
            order_line.dumps(dumper=AcqOrderLineNotificationDumper())
            for order_line in record.get_order_lines(
                includes=[AcqOrderLineStatus.APPROVED])
        ]
        data = {k: v for k, v in data.items() if v}
        return data
