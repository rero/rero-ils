# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

from invenio_search.api import DefaultFilter

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.stats_cfg.extensions import StatConfigDataExtension
from rero_ils.modules.stats_cfg.models import StatCfgIdentifier, \
    StatCfgMetadata
from rero_ils.modules.stats_cfg.permissions import permission_filter

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


class StatsCfgSearch(IlsRecordsSearch):
    """Statistics configuration search."""

    class Meta:
        """Search only on stats_cfg index."""

        index = 'stats_cfg'
        doc_types = None
        fields = ('*',)
        facets = {}

        default_filter = DefaultFilter(permission_filter)


class Stat_cfg(IlsRecord):
    """Statistics configuration class."""

    minter = stat_cfg_id_minter
    fetcher = stat_cfg_id_fetcher
    provider = StatCfgProvider
    model_cls = StatCfgMetadata

    _extensions = [
        StatConfigDataExtension()
    ]

    def update(self, data, commit=False, dbcommit=False, reindex=False):
        """Update data for record.

        The following fields:
        indicator, dist1, dist2, filters, org_pid, category
        cannot be changed if there is a report for the configuration.
        """
        # the update of the cfg is possible only if reports
        # were not yet created or the following fields have not been changed
        fields = ['indicator', 'dist1', 'dist2',
                  'filters', 'org_pid', 'category']
        record = self.get_record_by_pid(self.pid)
        if Stat_cfg.get_links_to_me(self.pid):
            for field in fields:
                if not record[field] == data[field]:
                    return

        super().update(data, commit=commit, dbcommit=dbcommit, reindex=reindex)
        return self

    @classmethod
    def get_cfgs(cls):
        """Get report configurations for system librarian.

        System librarian can see all reports configurations of the
        organisation.
        :returns: list of active configuration pids
        """
        search = StatsCfgSearch().filter('term', status='active').scan()
        return [s for s in search]

    @classmethod
    def get_links_to_me(cls, pid, get_pids=False):
        """Record links.

        :param pid: report configuration pid
        :param get_pids: if True list of linked pids
                         if False count of linked reports
        :return: dict with number of reports or reports pids
        """
        from rero_ils.modules.stats.api import StatsSearch
        links = {}

        # search for reports of configuration
        search = StatsSearch()\
            .filter('term', type='report')\
            .filter('term', config_pid=pid)

        if get_pids:
            search = search.source(['pid']).scan()
            reports = [s.pid for s in search]
        else:
            reports = search.count()

        # get number of reports or list of reports pids for configuration
        if reports:
            links['reports'] = reports
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete report config.

        :return: dict with number of reports or reports pids
        """
        cannot_delete = {}
        # Not possible to delete configuration if there are reports.
        links = Stat_cfg.get_links_to_me(self.pid)
        if links:
            cannot_delete['links'] = links
        return cannot_delete


class StatsCfgIndexer(IlsRecordsIndexer):
    """Indexing stats configuration in Elasticsearch."""

    record_cls = Stat_cfg

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='stacfg')
