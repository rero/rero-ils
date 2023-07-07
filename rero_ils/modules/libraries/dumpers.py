# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
        data.update({
            'name': record.get('name'),
            'address': record.get_address(LibraryAddressType.MAIN_ADDRESS),
            'shipping_informations':
                record.get('acquisition_settings', {})
                      .get('shipping_informations', {}),
            'billing_informations':
                record.get('acquisition_settings', {})
                      .get('billing_informations', {})
        })
        data = {k: v for k, v in data.items() if v}
        return data


class LibrarySerialClaimNotificationDumper(InvenioRecordsDumper):
    """Library dumper class for serial claim notification."""

    def dump(self, record, data):
        """Dump a library instance for serial claim notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        if 'serial_acquisition_settings' not in record:
            raise MissingDataException('library.serial_acquisition_settings')

        data.update({
            'name': record.get('name'),
            'address': record.get_address(LibraryAddressType.MAIN_ADDRESS),
            'shipping_informations':
                record.get('serial_acquisition_settings', {})
                      .get('shipping_informations', {}),
            'billing_informations':
                record.get('serial_acquisition_settings', {})
                      .get('billing_informations', {})
        })
        data = {k: v for k, v in data.items() if v}
        return data


class LibraryCirculationNotificationDumper(InvenioRecordsDumper):
    """Library dumper class for circulation notification."""

    def dump(self, record, data):
        """Dump a library instance for circulation notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        data.update({
            'pid': record.pid,
            'name': record.get('name'),
            'address': record.get('address'),
            'email': record.get('email')
        })
        return {k: v for k, v in data.items() if v}
