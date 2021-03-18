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

"""API for manipulating operation_logs."""

from functools import partial

from .models import OperationLogIdentifier, OperationLogMetadata, \
    OperationLogOperation
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
OperationLogProvider = type(
    'OperationLogProvider',
    (Provider,),
    dict(identifier=OperationLogIdentifier, pid_type='oplg')
)
# minter
operation_log_id_minter = partial(id_minter, provider=OperationLogProvider)
# fetcher
operation_log_id_fetcher = partial(id_fetcher, provider=OperationLogProvider)


class OperationLogsSearch(IlsRecordsSearch):
    """Operation log Search."""

    class Meta:
        """Search only on operation_log index."""

        index = 'operation_logs'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class OperationLog(IlsRecord):
    """OperationLog class."""

    minter = operation_log_id_minter
    fetcher = operation_log_id_fetcher
    provider = OperationLogProvider
    model_cls = OperationLogMetadata

    @classmethod
    def get_create_operation_log_by_resource_pid(cls, pid_type, record_pid):
        """Return a create operation log for a given resource and pid.

        :param pid_type: resource pid type.
        :param record_pid: record pid.
        """
        search = OperationLogsSearch()
        search = search.filter('term', record__pid=record_pid)\
            .filter('term', record__type=pid_type)\
            .filter('term', operation=OperationLogOperation.CREATE)
        oplgs = search.source(['pid']).scan()
        try:
            return OperationLog.get_record_by_pid(next(oplgs).pid)
        except StopIteration:
            return None


class OperationLogsIndexer(IlsRecordsIndexer):
    """Operation log indexing class."""

    record_cls = OperationLog

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(OperationLogsIndexer, self).bulk_index(
            record_id_iterator, doc_type='oplg')
