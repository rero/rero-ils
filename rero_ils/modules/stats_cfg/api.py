# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Statistics configuration for report."""
from functools import partial

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref

from .dumpers import indexer_dumper
from .models import StatCfgIdentifier, StatCfgMetadata

# provider
StatCfgProvider = type(
    'StatCfgProvider',
    (Provider,),
    dict(identifier=StatCfgIdentifier, pid_type='stacfg')
)
# minter
stat_cfg_id_minter = partial(id_minter, provider=StatCfgProvider)
# fetcher
stat_cfg_id_fetcher = partial(id_fetcher, provider=StatCfgProvider)


class StatsConfigurationSearch(IlsRecordsSearch):
    """Statistics configuration search."""

    class Meta:
        """Search only on stats_cfg index."""

        index = 'stats_cfg'
        doc_types = None
        fields = ('*',)
        facets = {}

        default_filter = None


class StatConfiguration(IlsRecord):
    """Statistics configuration class."""

    minter = stat_cfg_id_minter
    fetcher = stat_cfg_id_fetcher
    provider = StatCfgProvider
    model_cls = StatCfgMetadata
    enable_jsonref = False

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked reports
        :return: dict with number of reports or reports pids
        """
        from rero_ils.modules.stats.api.api import StatsSearch

        links = {}

        query = StatsSearch()\
            .filter('term', type='report')\
            .filter('term', config__pid=self.pid)

        if get_pids:
            query = query.source(['pid']).scan()
            reports = [s.pid for s in query]
        else:
            reports = query.count()

        # get number of reports or list of reports pids for configuration
        if reports:
            links['reports'] = reports
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete report config.

        :return: dict with number of reports or reports pids
        """
        cannot_delete = {}
        # It is not possible to delete configuration if there are reports.
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    @property
    def organisation_pid(self):
        """Shortcut for organisation pid."""
        library = extracted_data_from_ref(self.get('library'), data='record')
        return library.organisation_pid

    @property
    def library_pid(self):
        """Shortcut for library pid."""
        return extracted_data_from_ref(self.get('library'))


class StatsConfigurationIndexer(IlsRecordsIndexer):
    """Indexing stats configuration in Elasticsearch."""

    record_cls = StatConfiguration
    record_dumper = indexer_dumper

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='stacfg')
