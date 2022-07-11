# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

from .models import BudgetIdentifier, BudgetMetadata
from ..acq_accounts.api import AcqAccountsSearch
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..organisations.api import Organisation
from ..providers import Provider
from ..utils import sorted_pids

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


class Budget(IlsRecord):
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
    def is_active(self):
        """Check if the budget should be considered as active.

        To know if an budget is is_active, we need to check 'is_active' field.
        """
        return self.get('is_active')

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        links = {}
        query = AcqAccountsSearch().filter('term', budget__pid=self.pid)
        if get_pids:
            acq_accounts = sorted_pids(query)
        else:
            acq_accounts = query.count()
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

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='budg')
