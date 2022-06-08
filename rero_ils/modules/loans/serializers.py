# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Loans serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

from .api import Loan
from .models import LoanState
from ..documents.api import DocumentsSearch
from ..items.api import Item
from ..items.dumpers import ItemCirculationDumper
from ..libraries.api import Library


class LoanJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    # TODO :: will be refactored in next PR
    def postprocess_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        records = results.get('hits', {}).get('hits', [])
        for record in records:
            metadata = record.get('metadata', {})
            # Loan
            loan = Loan.get_record_by_pid(metadata.get('pid'))
            # Library name
            library_pid = metadata.get('library_pid')
            data = Library.get_record_by_pid(library_pid)
            metadata['library'] = {
                'pid': data['pid'],
                'name': data['name']
            }
            del metadata['library_pid']
            # Document
            document_pid = metadata.get('document_pid')
            search = DocumentsSearch().filter(
                'term', pid=document_pid)
            documents = list(search.scan())
            # check if the document still exists
            if documents:
                metadata['document'] = documents[0].to_dict()
                del metadata['document_pid']
            # Item
            item_pid = metadata.get('item_pid', {}).get('value')
            if item_pid:
                item = Item.get_record_by_pid(item_pid)
                # check if the item still exists
                if item:
                    metadata['item'] = \
                        item.dumps(dumper=ItemCirculationDumper())
                # Item loan
                if metadata['state'] == LoanState.ITEM_ON_LOAN:
                    metadata['overdue'] = loan.is_loan_overdue()
                    metadata['is_late'] = loan.is_loan_late()
                # Item request
                elif metadata['state'] in [
                    LoanState.PENDING,
                    LoanState.ITEM_AT_DESK,
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
                ]:
                    self._process_loan_pending_at_desk_in_transit_for_pickup(
                        metadata, item_pid)
                elif metadata['state'] in [
                    LoanState.ITEM_RETURNED,
                    LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
                    LoanState.CANCELLED
                ]:
                    self._process_loan_returned_in_transit_to_house_cancelled(
                        metadata, loan)
                del metadata['item_pid']
        return super(LoanJSONSerializer, self)\
            .postprocess_serialize_search(results, pid_fetcher)

    def _process_loan_pending_at_desk_in_transit_for_pickup(
            self, metadata, item_pid):
        """Process for PENDING, ITEM_AT_DESK, ITEM_IN_TRANSIT_FOR_PICKUP."""
        pickup_loc = Location.get_record_by_pid(
            metadata['pickup_location_pid'])
        metadata['pickup_name'] = \
            pickup_loc.get('pickup_name', pickup_loc.get('name'))
        if metadata['state'] == LoanState.ITEM_AT_DESK:
            metadata['rank'] = 0
        if metadata['state'] in [
            LoanState.PENDING,
            LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
        ]:
            patron = Patron.get_record_by_pid(
                metadata['patron_pid'])
            item = Item.get_record_by_pid(item_pid)
            metadata['rank'] = item.patron_request_rank(
                patron)

    def _process_loan_returned_in_transit_to_house_cancelled(
            self, metadata, loan):
        """Process for ITEM_RETURNED, ITEM_IN_TRANSIT_TO_HOUSE, CANCELLED."""
        metadata['pickup_library_name'] = Location\
            .get_record_by_pid(loan['pickup_location_pid'])\
            .get_library().get('name')
        metadata['transaction_library_name'] = Location\
            .get_record_by_pid(loan['transaction_location_pid'])\
            .get_library().get('name')


_json = LoanJSONSerializer(RecordSchemaJSONV1)
json_loan_search = search_responsify(_json, 'application/rero+json')
