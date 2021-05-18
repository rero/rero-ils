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

"""API for manipulating acquisition accounts."""

from functools import partial

from elasticsearch_dsl import Q
from flask_babelex import gettext as _

from .extensions import ParentAccountDistributionCheck
from .models import AcqAccountIdentifier, AcqAccountMetadata
from ..acq_invoices.api import AcquisitionInvoice, AcquisitionInvoicesSearch
from ..acq_order_lines.api import AcqOrderLine, AcqOrderLinesSearch
from ..acq_order_lines.models import AcqOrderLineStatus
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import extracted_data_from_ref, sorted_pids

AcqAccountProvider = type(
    'AcqAccountProvider',
    (Provider,),
    dict(identifier=AcqAccountIdentifier, pid_type='acac')
)
acq_account_id_minter = partial(id_minter, provider=AcqAccountProvider)
acq_account_id_fetcher = partial(id_fetcher, provider=AcqAccountProvider)


class AcqAccountsSearch(IlsRecordsSearch):
    """AcqAccountsSearch."""

    class Meta:
        """Search only on acquisition account index."""

        index = 'acq_accounts'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcqAccount(IlsRecord):
    """AcqAccount class."""

    minter = acq_account_id_minter
    fetcher = acq_account_id_fetcher
    provider = AcqAccountProvider
    model_cls = AcqAccountMetadata

    pids_exist_check = {
        'required': {
            'lib': 'library',
            'budg': 'budget'
        },
        'not_required': {
            'parent': 'acq_account',
            'org': 'organisation'
        }
    }

    _extensions = [ParentAccountDistributionCheck()]

    def __hash__(self):
        """Builtin function to return an hash for this account."""
        # TODO :: find a better hash method (more complete)
        return hash(str(self.id))

    @property
    def library_pid(self):
        """Shortcut for acquisition account library PID."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def library(self):
        """Shortcut to get related library."""
        return extracted_data_from_ref(self.get('library'), data='record')

    @property
    def organisation_pid(self):
        """Shortcut for acquisition account organisation PID."""
        return self.library.organisation_pid

    @property
    def parent(self):
        """Shortcut to get the parent acquisition account."""
        # NOTE FOR DEVELOPERS : It's a bad choice to write such kind of test :
        #
        #   > acc = AcqAccount.get_record_by_pid(1)
        #   > if acc.parent:
        #   >     return acc.parent.any_method()
        #
        # In this case, 4 DB calls are used because `parent` property return
        # a record object. For performance, it's better to store `parent` into
        # a temporary variable before testing and manipulate it.
        #
        #   > acc = AcqAccount.get_record_by_pid(1)
        #   > parent = acc.parent
        #   > if parent:
        #   >     return parent.any_method()
        #
        if self.get('parent'):
            return extracted_data_from_ref(self.get('parent'), data='record')

    @property
    def depth(self):
        """Get the depth of this account into the account structure.

        As an account can have a parent account, it's interesting to know the
        depth of this account. A root account has a depth of 0 ; each child has
        a depth of parent_depth + 1.
        """
        parent = self.parent
        return parent.depth + 1 if parent else 0

    @property
    def is_active(self):
        """Get if the account should be considerate as active.

        To know if an account is active, we need to check the related budget.
        This budget has a 'is_active' field.
        """
        from ..budgets.api import BudgetsSearch
        budget_id = extracted_data_from_ref(self.get('budget'))
        es = BudgetsSearch() \
            .filter('term', pid=budget_id) \
            .source(['is_active']).scan()
        return next(es).is_active or False

    @property
    def encumbrance_amount(self):
        """Get the encumbrance amount related to this account.

        This amount is the sum of :
          * Order lines related to this account depending of order lines
            status ; only "pending" order lines must be used to compute this
            amount.
          * Encumbrance of all children account

        @:return A tuple of encumbrance amount : First element if encumbrance
                 for this account, second element is the children encumbrance.
        """
        # Encumbrance of this account
        query = AcqOrderLinesSearch().filter('term', acq_account__pid=self.pid)
        if AcqOrderLineStatus.OPEN:
            pending_status = []
            for status in AcqOrderLineStatus.OPEN:
                pending_status.append(Q('term', status=status))
            query = query.query('bool', should=pending_status)

        query.aggs.metric('total_amount', 'sum', field='total_amount')
        results = query.execute()
        self_amount = results.aggregations.total_amount.value

        # Encumbrance of children accounts
        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        query.aggs.metric('total', 'sum', field='encumbrance_amount.total')
        results = query.execute()
        children_amount = results.aggregations.total.value

        return self_amount, children_amount

    @property
    def expenditure_amount(self):
        """Get the expenditure amount related to this account.

        This amount is the sum of :
          * Invoice lines related to this account depending of invoice lines
            status; only "received" invoice lines must be used to compute this
            amount.
          * expenditure of all children accounts

        @:return A tuple of expenditure amount : First element for self
                 expenditure amount, second element is the children
                 expenditure amount.
        """
        # Expenditure of children accounts
        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        query.aggs.metric('total', 'sum', field='expenditure_amount.total')
        results = query.execute()
        children_amount = results.aggregations.total.value

        # TODO :: compute the expenditure based on acq_invoices.
        self_amount = 0

        return self_amount, children_amount

    @property
    def remaining_balance(self):
        """Get the remaining balances for this account.

        The balance is computed from the initial account amount minus
        encumbrance and expenditure of myself, and distribution to children
        accounts.
        The total balance for this account is computed from the initial account
        minus the sum of (self encumbrance + children encumbrance) and the sum
        of (self expenditure + children expenditure).

        :return: A tuple with self balance and total balance
        """
        initial_amount = self.get('allocated_amount')
        encumbrance = self.encumbrance_amount
        expenditure = self.expenditure_amount

        self_balance = initial_amount \
            - self.distribution \
            - encumbrance[0] \
            - expenditure[0]
        total_balance = initial_amount \
            - sum(list(self.encumbrance_amount)) \
            - sum(list(self.expenditure_amount))

        return self_balance, total_balance

    @property
    def distribution(self):
        """Get the amount distributed to children accounts.

        The amount to be distributed is the sum of initial amount of direct
        children accounts. If this account has 2 children, 'AccountA' and
        'AccountB', with both an allocated amount of 2000, then the amount to
        be distributed by the parent account is 4000.
        The distribution cannot exceed the allocated amount of the account.
        """
        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        query.aggs.metric('total_amount', 'sum', field='allocated_amount')
        results = query.execute()
        return results.aggregations.total_amount.value

    def transfer_fund(self, target_account, amount):
        """Transfer funds between two accounts.

        To transfer funds between this account and the specified target
        account. To do that, the source account must have enough available
        money.
        :param target_account: the target account as AcqAccount instance.
        :param amount: the amount to transfer to target account.
        :raise ValueError: if transfer amount is greater than source availabe
               balance.
        """
        # First check if :
        #   * target account == source account
        #   * requested transfer amount is available on source account.
        if self == target_account:
            raise ValueError(_('Cannot transfer fund to myself.'))
        if amount > self.remaining_balance[0]:
            msg = _('Not enough available money from source account.')
            raise ValueError(msg)

        # CASE 1 : target account is an ancestor of source account.
        #   In this case, decrease the allocated amount from source and all
        #   ancestor accounts until reaching the target account
        source_ancestors = list(self.get_ancestors())
        if target_account in source_ancestors:
            for acc in ([self] + source_ancestors):
                if acc == target_account:
                    break
                acc['allocated_amount'] -= amount
                acc.update(acc, dbcommit=True, reindex=False)
            self.reindex()  # index myself and all my ancestors
            return

        # CASE 2 : target and source are in the same account tree.
        #   In this case, we need to
        #     * find the common ancestor of source and target account.
        #     * from source account to common ancestor (not included), we need
        #       to decrease the allocated amount.
        #     * from common ancestor (not included) to target account, we need
        #       to increase the allocated amount.
        target_ancestors = list(target_account.get_ancestors())
        common_ancestors = list(
            set([self] + source_ancestors) &
            set([target_account] + target_ancestors)
        )
        common_ancestor = None
        if common_ancestors:
            common_ancestor = max(common_ancestors, key=lambda a: a.depth)
        # If we found a common ancestor, we are in the same tree
        if common_ancestor:
            for acc in ([self] + source_ancestors):
                if acc == common_ancestor:
                    break
                acc['allocated_amount'] -= amount
                # Note : We need to reindex during update, to update parent
                # account balances. Without this reindex, the pre_commit hook
                # will detect a problem
                acc.update(acc, dbcommit=True, reindex=True)

            ancestors_to_apply = []
            for acc in target_ancestors:
                if acc == common_ancestor:
                    break
                ancestors_to_apply.append(acc)
            for acc in reversed([target_account] + ancestors_to_apply):
                acc['allocated_amount'] += amount
                acc.update(acc, dbcommit=True, reindex=False)
            target_account.reindex()
            return

        # CASE 3 : target and source aren't in the same account tree.
        #   * from source account to source root account (included), decrease
        #     the allocated amount.
        #   * from target root account to target account, increase the
        #     allocated amount.
        for acc in ([self] + source_ancestors):
            acc['allocated_amount'] -= amount
            acc.update(acc, dbcommit=True, reindex=True)
        for acc in reversed([target_account] + target_ancestors):
            acc['allocated_amount'] += amount
            acc.update(acc, dbcommit=True, reindex=False)
        target_account.reindex()

    def get_related_order_lines(self, output=None):
        """Get order lines related to this account.

        :param output: the output method. 'count', 'pids' or None
        :return a generator of related order lines (or length).
        """
        def _list_object():
            for hit in query.source(['pid']).scan():
                yield AcqOrderLine.get_record_by_pid(hit.pid)

        query = AcqOrderLinesSearch().filter('term', acq_account__pid=self.pid)
        if output == 'count':
            return query.count()
        elif output == 'pids':
            return sorted_pids(query)
        else:
            return _list_object()

    def get_ancestors(self):
        """Get all ancestors related to this account.

        :return a list of ancestor accounts.
        """
        parent = self.parent
        if parent:
            return [parent] + parent.get_ancestors()
        return []

    def get_children(self, output=None):
        """Get children accounts related to this account.

        :param output: output method. 'count', 'pids' or None
        :return a generator of children accounts (or length).
        """
        def _list_object():
            for hit in query.source(['pid']).scan():
                yield AcqAccount.get_record_by_pid(hit.pid)

        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        if output == 'count':
            return query.count()
        elif output == 'pids':
            return sorted_pids(query)
        else:
            return _list_object()

    def get_related_invoices(self, output=None):
        """Get invoices related to this account.

        :param output: output method. 'count', 'pids' or None
        :return a generator of related invoices (or length).
        """
        def _list_object():
            for hit in query.source(['pid']).scan():
                yield AcquisitionInvoice.get_record_by_pid(hit.pid)

        query = AcquisitionInvoicesSearch()\
            .filter('term', invoice_items__acq_account__pid=self.pid)
        if output == 'count':
            return query.count()
        elif output == 'pids':
            return sorted_pids(query)
        else:
            return _list_object()

    def get_links_to_me(self, get_pids=False):
        """Get resources linked to this object.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        output = 'pids' if get_pids else 'count'
        links = {
            'acq_order_lines': self.get_related_order_lines(output=output),
            'acq_accounts': self.get_children(output=output),
            'acq_invoices': self.get_related_invoices(output=output)
        }
        links = {k: v for k, v in links.items() if v}
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        reasons = {
            'links': self.get_links_to_me()
        }
        reasons = {k: v for k, v in reasons.items() if v}
        return reasons


class AcqAccountsIndexer(IlsRecordsIndexer):
    """Indexing AcqAccount in Elasticsearch."""

    record_cls = AcqAccount

    def index(self, record):
        """Indexing an acq account record (and parent if needed)."""
        return_value = super().index(record)
        parent_account = record.parent
        if parent_account:
            parent_account.reindex()
        return return_value

    def delete(self, record):
        """Delete a record from indexer."""
        parent = record.parent
        super().delete(record)
        if parent:
            parent.reindex()

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='acac')
