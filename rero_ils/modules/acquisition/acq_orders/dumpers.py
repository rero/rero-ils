# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition order dumpers."""

from datetime import date

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.acquisition.acq_order_lines.dumpers import (
    AcqOrderLineNotificationDumper,
)
from rero_ils.modules.acquisition.acq_order_lines.models import AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderNoteType
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.libraries.dumpers import LibraryAcquisitionNotificationDumper
from rero_ils.modules.utils import get_ref_for_pid
from rero_ils.modules.vendors.api import Vendor
from rero_ils.modules.vendors.dumpers import VendorAcquisitionNotificationDumper


class AcqOrderNotificationDumper(InvenioRecordsDumper):
    """Dumper class for acquisition order notification."""

    def dump(self, record, data):
        """Dump an AcqOrder instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        today = date.today().strftime("%Y-%m-%d")
        data.update(
            {
                "reference": record.get("reference"),
                "order_date": record.get("order_date", today),
                "note": record.get_note(AcqOrderNoteType.VENDOR),
            }
        )
        library = Library.get_record_by_pid(record.library_pid)
        data["library"] = library.dumps(dumper=LibraryAcquisitionNotificationDumper())
        vendor = Vendor.get_record_by_pid(record.vendor_pid)
        data["vendor"] = vendor.dumps(dumper=VendorAcquisitionNotificationDumper())
        data["order_lines"] = [
            order_line.dumps(dumper=AcqOrderLineNotificationDumper())
            for order_line in record.get_order_lines(includes=[AcqOrderLineStatus.APPROVED])
        ]
        return {k: v for k, v in data.items() if v}


class AcqOrderHistoryDumper(InvenioRecordsDumper):
    """Dumper class for acquisition order history API."""

    def dump(self, record, data):
        """Dump an AcqOrder instance for acquisition order history API.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        label = record.get("reference")
        if budget := record.budget:
            label = budget.name
        return {
            "$ref": get_ref_for_pid("acor", record.pid),
            "label": label,
            "description": record.get("reference"),
            "created": record.created.isoformat(),
            "updated": record.updated.isoformat(),
        }
