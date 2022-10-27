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

"""API for manipulating budgets."""

from functools import partial

from elasticsearch import NotFoundError

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccount, \
    AcqAccountsSearch
from rero_ils.modules.acquisition.api import AcquisitionIlsRecord
from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import sorted_pids

from .models import BudgetIdentifier, BudgetMetadata

# provider
BudgetProvider = type(
    'BudgetProvider',
    (Provider,),
    dict(identifier=BudgetIdentifier, pid_type='budg')
)
# minter
budget_id_minter = partial(id_minter, provider=BudgetProvider)
# fetcher
budget_id_fetcher = partial(id_fetcher, provider=BudgetProvider)


class BudgetsSearch(IlsRecordsSearch):
    """BudgetsSearch."""

    class Meta:
        """Search only on budget index."""

        index = 'budgets'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Budget(AcquisitionIlsRecord):
    """Budget class."""

    minter = budget_id_minter
    fetcher = budget_id_fetcher
    provider = BudgetProvider
    model_cls = BudgetMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation'
        }
    }

    @property
    def name(self):
        """Shortcut for budget name."""
        return self.get('name')

    @property
    def is_active(self):
        """Check if the budget should be considered as active."""
        return self.get('is_active', False)

    def get_related_accounts(self):
        """Get account related to this budget.

        :rtype: an `AcqAccount` generator
        """
        query = AcqAccountsSearch() \
            .filter('term', budget__pid=self.pid) \
            .source(False)
        for hit in query.scan():
            yield AcqAccount.get_record(hit.meta.id)

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        links = {}
        query = AcqAccountsSearch().filter('term', budget__pid=self.pid)
        acq_accounts = sorted_pids(query) if get_pids else query.count()
        if acq_accounts:
            links['acq_accounts'] = acq_accounts
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        # Note: not possible to delete records attached to rolled_over budget.
        if not self.is_active:
            cannot_delete['links'] = {'rolled_over': True}
            return cannot_delete
        if others := self.reasons_to_keep():
            cannot_delete['others'] = others
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        return cannot_delete

    def reasons_to_keep(self):
        """Reasons aside from record_links to keep a budget."""
        others = {}
        organisation = Organisation.get_record_by_pid(self.organisation_pid)
        if organisation.get('current_budget_pid') == self.pid:
            others['is_default'] = True
        return others


class BudgetsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = Budget

    def index(self, record):
        """Indexing an budget record."""
        BudgetsIndexer._check_is_active_changed(record)
        return super().index(record)

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='budg')

    @classmethod
    def _check_is_active_changed(cls, record):
        """Detect is `is_active` field changed.

        In this case, we need to reindex related accounts to set them as
        inactive into the AcqAccount ES index.

        :param record: the record to index.
        """
        try:
            original_record = BudgetsSearch().get_record_by_pid(record.pid)
            if record.is_active != original_record['is_active']:
                for account in record.get_related_accounts():
                    account.reindex()
        except NotFoundError:
            pass
