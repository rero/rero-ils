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

"""API for manipulating statistics."""

from functools import partial

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref

from ..extensions import StatisticsDumperExtension
from ..models import StatIdentifier, StatMetadata

# provider
StatProvider = type(
    'StatProvider',
    (Provider,),
    dict(identifier=StatIdentifier, pid_type='stat')
)
# minter
stat_id_minter = partial(id_minter, provider=StatProvider)
# fetcher
stat_id_fetcher = partial(id_fetcher, provider=StatProvider)


class StatsSearch(IlsRecordsSearch):
    """Statistics search."""

    class Meta:
        """Search only on stats index."""

        index = 'stats'
        doc_types = None
        fields = ('*',)
        facets = {}

        default_filter = None


class Stat(IlsRecord):
    """Statistics class."""

    minter = stat_id_minter
    fetcher = stat_id_fetcher
    provider = StatProvider
    model_cls = StatMetadata

    _extensions = [
        StatisticsDumperExtension()
    ]

    def update(self, data, commit=True, dbcommit=False, reindex=False):
        """Update data for record."""
        super().update(data, commit, dbcommit, reindex)
        return self

    @property
    def organisation_pid(self):
        """Get organisation pid from the config for report."""
        if ref := self.get('config', {}).get('organisation', {}).get('$ref'):
            return extracted_data_from_ref(ref)


class StatsIndexer(IlsRecordsIndexer):
    """Indexing stats in Elasticsearch."""

    record_cls = Stat

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='stat')
