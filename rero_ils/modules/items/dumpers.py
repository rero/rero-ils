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

"""Items dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.documents.dumpers import \
    TitleDumper as DocumentTitleDumper
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.holdings.dumpers import ClaimIssueHoldingDumper
from rero_ils.modules.libraries.dumpers import \
    LibrarySerialClaimNotificationDumper
from rero_ils.modules.vendors.dumpers import \
    VendorAcquisitionNotificationDumper


class ItemNotificationDumper(InvenioRecordsDumper):
    """Item dumper class for notification."""

    def dump(self, record, data):
        """Dump an item instance for notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        location = record.get_location()
        data = {
            'pid': record.pid,
            'barcode': record.get('barcode'),
            'call_numbers': record.call_numbers,
            'location_name': location.get('name'),
            'library_name': location.get_library().get('name'),
            'enumerationAndChronology': record.get('enumerationAndChronology')
        }
        data = {k: v for k, v in data.items() if v}
        return data


class ItemCirculationDumper(InvenioRecordsDumper):
    """Item dumper class for circulation."""

    def dump(self, record, data):
        """Dump an item instance for circulation.

        :param record: the record to dump.
        :param data: the initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        # Dump all information about the item
        data.update(record.replace_refs().dumps())
        data = {k: v for k, v in data.items() if v}

        # Add the inherited call numbers from parent holding record if item
        # call numbers is empty.
        if all(k not in data for k in ['call_number', 'second_call_number']):
            holding = Holding.get_record_by_pid(record.holding_pid)
            data['call_number'] = holding.get('call_number')
            data['second_call_number'] = holding.get('second_call_number')
            data = {k: v for k, v in data.items() if v}

        return data


class ClaimIssueNotificationDumper(InvenioRecordsDumper):
    """Item issue dumper for claim notification."""

    def dump(self, record, data):
        """Dump an item issue for claim notification generation."""
        assert record.is_issue, 'record must be an `ItemIssue` resource'
        assert (holding := record.holding), \
            'record must be related to an existing `Holding`'

        data.update({
            'vendor': holding.vendor.dumps(
                dumper=VendorAcquisitionNotificationDumper()),
            'document': holding.document.dumps(
                dumper=DocumentTitleDumper()),
            'library': holding.library.dumps(
                dumper=LibrarySerialClaimNotificationDumper()),
            'holdings': holding.dumps(dumper=ClaimIssueHoldingDumper()),
            'enumerationAndChronology': record.enumerationAndChronology,
            'claim_counter': record.claims_count
        })

        return {k: v for k, v in data.items() if v}
