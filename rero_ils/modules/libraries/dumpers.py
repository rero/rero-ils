# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.commons.exceptions import MissingDataException
from rero_ils.modules.libraries.models import LibraryAddressType


class LibraryAcquisitionNotificationDumper(InvenioRecordsDumper):
    """Library dumper class for acquisition order notification."""

    def dump(self, record, data):
        """Dump a library instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update(
            {
                "name": record.get("name"),
                "address": record.get_address(LibraryAddressType.MAIN_ADDRESS),
                "shipping_informations": record.get("acquisition_settings", {}).get("shipping_informations", {}),
                "billing_informations": record.get("acquisition_settings", {}).get("billing_informations", {}),
            }
        )
        return {k: v for k, v in data.items() if v}


class LibrarySerialClaimNotificationDumper(InvenioRecordsDumper):
    """Library dumper class for serial claim notification."""

    def dump(self, record, data):
        """Dump a library instance for serial claim notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        if "serial_acquisition_settings" not in record:
            raise MissingDataException("library.serial_acquisition_settings")

        data.update(
            {
                "name": record.get("name"),
                "address": record.get_address(LibraryAddressType.MAIN_ADDRESS),
                "shipping_informations": record.get("serial_acquisition_settings", {}).get("shipping_informations", {}),
                "billing_informations": record.get("serial_acquisition_settings", {}).get("billing_informations", {}),
            }
        )
        return {k: v for k, v in data.items() if v}


class LibraryCirculationNotificationDumper(InvenioRecordsDumper):
    """Library dumper class for circulation notification."""

    def dump(self, record, data):
        """Dump a library instance for circulation notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        data.update(
            {
                "pid": record.pid,
                "name": record.get("name"),
                "address": record.get("address"),
                "email": record.get("email"),
            }
        )
        return {k: v for k, v in data.items() if v}
