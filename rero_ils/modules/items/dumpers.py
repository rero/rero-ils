# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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
from copy import deepcopy

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.collections.api import CollectionsSearch
from rero_ils.modules.commons.exceptions import MissingDataException
from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dumpers import \
    TitleDumper as DocumentTitleDumper
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.holdings.dumpers import ClaimIssueHoldingDumper
from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.libraries.dumpers import \
    LibrarySerialClaimNotificationDumper
from rero_ils.modules.loans.dumpers import \
    CirculationDumper as LoanCirculationDumper
from rero_ils.modules.locations.api import Location
from rero_ils.modules.vendors.dumpers import VendorClaimIssueNotificationDumper


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
        if item_type_pid := record.item_type_pid:
            if item_type := ItemType.get_record_by_pid(item_type_pid):
                data['item_type'] = item_type['name']
        if temporary_item_type_pid := record.temporary_item_type_pid:
            if temporary_item_type := ItemType.get_record_by_pid(
                    temporary_item_type_pid):
                data['temporary_item_type'] = temporary_item_type['name']
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
        if not record.is_issue:
            raise TypeError('record must be an `ItemIssue` resource')
        if not (holding := record.holding):
            raise MissingDataException('item.holding')
        if not (vendor := holding.vendor):
            raise MissingDataException('item.holding.vendor')

        data.update({
            'vendor': vendor.dumps(
                dumper=VendorClaimIssueNotificationDumper()),
            'document': holding.document.dumps(
                dumper=DocumentTitleDumper()),
            'library': holding.library.dumps(
                dumper=LibrarySerialClaimNotificationDumper()),
            'holdings': holding.dumps(
                dumper=ClaimIssueHoldingDumper()),
            'enumerationAndChronology': record.enumerationAndChronology,
            'claim_counter': record.claims_count
        })
        return {k: v for k, v in data.items() if v is not None}


class CirculationActionDumper(InvenioRecordsDumper):
    """Item issue dumper for circulation actions."""

    def dump(self, record, data):
        """Dump an item for circulation actions."""
        item = record.replace_refs()
        data = deepcopy(dict(item))
        document = Document.get_record_by_pid(item['document']['pid'])
        doc_data = document.dumps()
        data['document']['title'] = doc_data['title']

        location = Location.get_record_by_pid(item['location']['pid'])
        loc_data = deepcopy(dict(location))
        data['location']['name'] = loc_data['name']
        # TODO: check if it is required
        data['location']['organisation'] = {
            'pid': record.organisation_pid
        }

        # add library and location name on same field (used for sorting)
        library = location.get_library()
        data['library_location_name'] = \
            f'{library["name"]}: {data["location"]["name"]}'

        data['actions'] = list(record.actions)

        # add the current pending requests count
        data['current_pending_requests'] = record.get_requests(output='count')
        # add metadata of the first pending request
        requests = record.get_requests(sort_by='_created')
        if first_request := next(requests, None):
            data['pending_loans'] = [
                first_request.dumps(LoanCirculationDumper())
            ]
        # add temporary location name
        if temporary_location_pid := item.get('temporary_location', {}).get(
            'pid'
        ):
            data['temporary_location']['name'] = Location.get_record_by_pid(
                temporary_location_pid).get('name')
        # add collections
        results = CollectionsSearch().active_by_item_pid(item['pid'])\
            .params(preserve_order=True).source('title').scan()
        if collections := [collection.title for collection in results]:
            data['collections'] = collections
        return data
