# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""API for manipulating ill_requests."""

from functools import partial

from .models import ILLRequestIdentifier
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..locations.api import Location
from ..minters import id_minter
from ..providers import Provider

# provider
ILLRequestProvider = type(
    'ILLRequestProvider',
    (Provider,),
    dict(identifier=ILLRequestIdentifier, pid_type='illr')
)
# minter
ill_request_id_minter = partial(id_minter, provider=ILLRequestProvider)
# fetcher
ill_request_id_fetcher = partial(id_fetcher, provider=ILLRequestProvider)


class ILLRequestsSearch(IlsRecordsSearch):
    """ILLRequestsSearch."""

    class Meta:
        """Search only on ill_request index."""

        index = 'ill_requests'
        doc_types = None


class ILLRequest(IlsRecord):
    """ILLRequest class."""

    minter = ill_request_id_minter
    fetcher = ill_request_id_fetcher
    provider = ILLRequestProvider

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        If record is a copy request (copy==true) then `pages` property is
        required
        """
        if self.is_copy and self.get('pages') is None:
            return 'Required property : `pages`'
        return True

    @property
    def is_copy(self):
        """Is request is a request copy."""
        return self.get('copy', False)

    @property
    def patron_pid(self):
        """Get patron pid for ill_request."""
        return self.replace_refs()['patron']['pid']

    @property
    def organisation_pid(self):
        """Get organisation pid for ill_request."""
        return self.get_pickup_location().organisation_pid

    def get_pickup_location(self):
        """Get the pickup location."""
        location_pid = self.replace_refs()['pickup_location']['pid']
        return Location.get_record_by_pid(location_pid)


class ILLRequestsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = ILLRequest

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(ILLRequestsIndexer, self).bulk_index(record_id_iterator,
                                                   doc_type='illr')
