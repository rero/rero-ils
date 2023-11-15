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

"""API for manipulating ill_requests."""

from datetime import datetime, timezone
from functools import partial

from dateutil.relativedelta import *
from elasticsearch_dsl.query import Q
from flask import current_app
from flask_babel import gettext as _

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.locations.api import Location
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref

from .extensions import IllRequestOperationLogObserverExtension
from .models import ILLRequestIdentifier, ILLRequestMetadata, \
    ILLRequestNoteStatus, ILLRequestStatus

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

    def get_ill_requests_total_for_patron(self, patron_pid):
        """Get the total number of ill requests filtered by date for a patron.

        Months defined in config.py.

        :param patron_pid: the patron pid being searched.
        :return: return total of ill requests.
        """
        months = current_app.config.get('RERO_ILS_ILL_HIDE_MONTHS', 6)
        date_delta = datetime.now(timezone.utc) - relativedelta(months=months)
        filters = Q(
            'range',
            _created={'lte': 'now', 'gte': date_delta}
        )
        filters |= Q('term', status=ILLRequestStatus.PENDING)
        filters &= Q('term', patron__pid=patron_pid)
        return self.filter(filters).count()


class ILLRequest(IlsRecord):
    """ILLRequest class."""

    minter = ill_request_id_minter
    fetcher = ill_request_id_fetcher
    provider = ILLRequestProvider
    model_cls = ILLRequestMetadata

    _extensions = [
        IllRequestOperationLogObserverExtension()
    ]

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        * If record is a copy request (copy==true) then `pages` property is
          required
        * Ensures that only one note of each type is present.
        """
        if self.is_copy and self.get('pages') is None:
            return 'Required property : `pages`'

        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return _('Can not have multiple notes of the same type.')

        return True

    @classmethod
    def _build_requests_query(cls, patron_pid, status=None):
        """Private function to build a request query linked to a patron."""
        query = ILLRequestsSearch() \
            .filter('term', patron__pid=patron_pid)
        if status:
            query = query.filter('term', status=status)
        return query

    @classmethod
    def get_request_pids_by_patron_pid(cls, patron_pid, status=None):
        """Get request pids related to a patron pid.

        :param patron_pid: the patron pid
        :param status: the requests status
        :return a generator of request pid
        """
        query = cls._build_requests_query(patron_pid, status)
        results = query.source('pid').scan()
        for result in results:
            yield result.pid

    @classmethod
    def get_requests_by_patron_pid(cls, patron_pid, status=None):
        """Get request pids related to a patron pid.

        :param patron_pid: the patron pid
        :param status: the requests status
        :return a generator of ILLRequest
        """
        for pid in cls.get_request_pids_by_patron_pid(patron_pid, status):
            yield ILLRequest.get_record_by_pid(pid)

    @property
    def is_copy(self):
        """Is request is a request copy."""
        return self.get('copy', False)

    @property
    def patron_pid(self):
        """Get patron pid for ill_request."""
        return extracted_data_from_ref(self.get('patron'))

    @property
    def organisation_pid(self):
        """Get organisation pid for ill_request."""
        return self.get_pickup_location().organisation_pid

    @property
    def public_note(self):
        """Get the public note for ill_requests."""
        notes = [note.get('content') for note in self.get('notes', [])
                 if note.get('type') == ILLRequestNoteStatus.PUBLIC_NOTE]
        return next(iter(notes or []), None)

    def get_pickup_location(self):
        """Get the pickup location."""
        location_pid = extracted_data_from_ref(self.get('pickup_location'))
        return Location.get_record_by_pid(location_pid)

    def get_library(self):
        """Get the library linked to the ill_request."""
        return self.get_pickup_location().get_library()


class ILLRequestsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = ILLRequest

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='illr')
