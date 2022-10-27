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

"""RERO-ILS Loan resource serializers for JSON format."""
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.dumpers import ItemCirculationDumper
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.dumpers import PatronPropertiesDumper
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer

from ..api import Loan


class LoanJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `Loan` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result."""

        def _post_process_search_request_hit(metadata, item):
            """Adds some information about a request."""
            loc = self.get_resource(
                LocationsSearch(), metadata.get('pickup_location_pid'))
            metadata.update({
                'pickup_name': loc.get('pickup_name', loc.get('name')),
                'rank': 0
            })
            if metadata['state'] not in LoanState.ITEM_AT_DESK:
                patron_pid = metadata.get('patron', {}).get('pid')
                patron = self.get_resource(Patron, patron_pid)
                metadata['rank'] = item.patron_request_rank(patron)

        def _post_process_search_concluded_hit(metadata, loan):
            """Adds some information about a concluded loan."""
            ploc_pid = loan.get('pickup_location_pid')
            ploc = self.get_resource(Location, ploc_pid) or {}
            plib = self.get_resource(Library, ploc.library_pid) or {}
            metadata['pickup_library_name'] = plib.get('name')
            tloc_pid = loan.get('transaction_location_pid')
            tloc = self.get_resource(Location, tloc_pid) or {}
            tlib = self.get_resource(Library, tloc.library_pid) or {}
            metadata['transaction_library_name'] = tlib.get('name')

        metadata = hit.get('metadata', {})
        # UPDATE LIBRARY INFORMATION
        #   create a new `library` dictionary entry containing library name and
        #   library pid. Remove the unnecessary `library_pid` entry.
        if library_pid := metadata.pop('library_pid', None):
            library = self.get_resource(Library, library_pid)
            metadata['library'] = {
                'pid': library_pid,
                'name': library['name']
            }
        # DUMP DOCUMENT INFORMATION
        #   Replace the `document_pid` reference by the known ElasticSearch
        #   data related to this document.
        if document_pid := metadata.pop('document_pid', None):
            document = self.get_resource(DocumentsSearch(), document_pid)
            metadata['document'] = document

        # DUMP PATRON INFORMATION
        #   Replace the `patron_pid` reference by some known ElasticSearch
        #   data related to this patron
        if patron_pid := metadata.pop('patron_pid', None):
            patron = self.get_resource(Patron, patron_pid)
            metadata['patron'] = patron.dumps(
                dumper=PatronPropertiesDumper(['formatted_name']))

        # DUMP ITEM INFORMATION
        #   Replace the `item_pid` reference by some specific item metadata.
        #   Complete these item metadata with some useful information depending
        #   on the current loan state.
        if item_pid := metadata.pop('item_pid', {}).get('value'):
            item = Item.get_record_by_pid(item_pid)
            loan = Loan.get_record_by_pid(metadata.get('pid'))
            if item:
                metadata['item'] = item.dumps(dumper=ItemCirculationDumper())
            # Add some specific information depending on loan state
            loan_state = metadata.get('state')
            if loan_state == LoanState.ITEM_ON_LOAN:
                metadata['overdue'] = loan.is_loan_overdue()
                metadata['is_late'] = loan.is_loan_late()
            elif loan_state in LoanState.REQUEST_STATES:
                _post_process_search_request_hit(metadata, item)
            elif loan_state in LoanState.CONCLUDED + [
                 LoanState.ITEM_IN_TRANSIT_TO_HOUSE]:
                _post_process_search_concluded_hit(metadata, loan)

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result.

        :param aggregations: the dictionary representing ElasticSearch
                             aggregations section.
        """

        def _get_buckets(parent, bucket_name: str) -> list:
            return parent.get(bucket_name, {}).get('buckets', [])

        def _enrich_buckets(buckets, search_class, attribute):
            JSONSerializer.enrich_bucket_with_data(
                buckets, search_class, attribute)

        aggr_ptty = _get_buckets(aggregations, 'patron_type')
        _enrich_buckets(aggr_ptty, PatronTypesSearch, 'name')

        # Add a `name` for all entries of the all library/location structure.
        # Owning library & location
        aggr_lib = _get_buckets(aggregations, 'owner_library')
        _enrich_buckets(aggr_lib, LibrariesSearch, 'name')
        for lib_term in aggr_lib:
            aggr_loc = _get_buckets(lib_term, 'owner_location')
            _enrich_buckets(aggr_loc, LocationsSearch, 'name')
        # Transaction library & location
        aggr_lib = _get_buckets(aggregations, 'transaction_library')
        _enrich_buckets(aggr_lib, LibrariesSearch, 'name')
        for lib_term in aggr_lib:
            aggr_loc = _get_buckets(lib_term, 'transaction_location')
            _enrich_buckets(aggr_loc, LocationsSearch, 'name')
        # Pickup library & location
        aggr_lib = _get_buckets(aggregations, 'pickup_library')
        _enrich_buckets(aggr_lib, LibrariesSearch, 'name')
        for lib_term in aggr_lib:
            aggr_loc = _get_buckets(lib_term, 'pickup_location')
            _enrich_buckets(aggr_loc, LocationsSearch, 'name')

        # Add configuration for `end_date` and `request_expire_date`
        #   ES `date_histogram` facet need some configuration settings to
        #   display the widget.
        for aggr_name in ['end_date', 'request_expire_date']:
            aggr = aggregations.get(aggr_name, {})
            JSONSerializer.add_date_range_configuration(aggr)

        # Miscellaneous status
        #   The `misc_status` aggregation buckets are based on ES filters
        #   queries. We need to rebuild this aggregation to display each
        #   filter query hit as a 'classic' term facet hit.
        if misc_aggr := aggregations.get('misc_status', {}).get('buckets'):
            aggregations['misc_status']['buckets'] = [
                {'key': term, 'doc_count': hit['doc_count']}
                for term, hit in misc_aggr.items()
                if hit.get('doc_count')
            ]
