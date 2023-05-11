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

"""Vendores dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class VendorAcquisitionNotificationDumper(InvenioRecordsDumper):
    """Vendor dumper class for acquisition order notification."""

    def dump(self, record, data):
        """Dump a vendor instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update({
            'name': record.get('name'),
            'language': record.get('communication_language', 'eng'),
            'email': record.order_email
        })
        data = {k: v for k, v in data.items() if v}
        return data


class VendorClaimIssueNotificationDumper(InvenioRecordsDumper):
    """Vendor dumper class for claim issue notification."""

    def dump(self, record, data):
        """Dump a vendor instance for claim issue notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update({
            'name': record.get('name'),
            'language': record.get('communication_language', 'eng'),
            'email': record.serial_email
        })
        data = {k: v for k, v in data.items() if v}
        return data
