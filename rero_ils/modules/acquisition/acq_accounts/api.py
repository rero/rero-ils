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

"""API for manipulating acquisition accounts."""

from functools import partial

from elasticsearch_dsl import Q
from flask_babel import gettext as _

from rero_ils.modules.acquisition.acq_invoices.api import \
    AcquisitionInvoicesSearch
from rero_ils.modules.acquisition.acq_order_lines.api import \
    AcqOrderLinesSearch
from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_receipt_lines.api import \
    AcqReceiptLinesSearch
from rero_ils.modules.acquisition.acq_receipts.api import AcqReceiptsSearch
from rero_ils.modules.acquisition.api import AcquisitionIlsRecord
from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, get_objects, \
    sorted_pids

from .extensions import ParentAccountDistributionCheck
from .models import AcqAccountExceedanceType, AcqAccountIdentifier, \
    AcqAccountMetadata

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


class AcqAccount(AcquisitionIlsRecord):
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

    _extensions = [
        ParentAccountDistributionCheck()
    ]

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition Order Line record."""
        # In order to check if some fields value are unique we need to ensure
        # that object has been indexed just after the creation.
        # TODO :: Maybe a better approach should be pass by `resource.service`
        #         and/or always use REST API.
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def __hash__(self):
        """Builtin function to return an hash for this account."""
        # TODO :: find a better hash method (more complete)
        return hash(str(self.id))

    @property
    def name(self):
        """Shortcut for acquisition account name."""
        return self.get('name')

    @property
    def library_pid(self):
        """Shortcut for acquisition account library PID."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def library(self):
        """Shortcut to get related library."""
        return extracted_data_from_ref(self.get('library'), data='record')

    @property
    def budget(self):
        """Shortcut to get related budget."""
        return extracted_data_from_ref(self.get('budget'), data='record')

    @property
    def organisation_pid(self):
        """Shortcut for acquisition account organisation PID."""
        return self.library.organisation_pid

    @property
    def parent_pid(self):
        """Shortcut to get the parent acquisition account pid."""
        if parent := self.get('parent'):
            return extracted_data_from_ref(parent)

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
        #   > if parent := acc.parent:
        #   >     return parent.any_method()
        if parent_pid := self.parent_pid:
            return AcqAccount.get_record_by_pid(parent_pid)

    @property
    def is_root(self):
        """Check if the account is a root account."""
        return 'parent' not in self

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
        """Check if the account should be considered as active.

        To know if an account is is_active, we need to check the related
        budget. This budget has an 'is_active' field.
        """
        budget = extracted_data_from_ref(self.get('budget'), data='record')
        return budget.is_active if budget else False

    @property
    def encumbrance_amount(self):
        """Get the encumbrance amount related to this account.

        This amount is the sum of :
          * APPROVED or ORDERED acqz order lines related to this account.
          * Encumbrance of all children account

        :return A tuple of encumbrance amount : First element if encumbrance
                 for this account, second element is the children encumbrance.
        """
        # Encumbrance of this account
        status_list = [
            AcqOrderLineStatus.APPROVED,
            AcqOrderLineStatus.ORDERED,
            AcqOrderLineStatus.PARTIALLY_RECEIVED
        ]
        query = AcqOrderLinesSearch()\
            .filter('term', acq_account__pid=self.pid)\
            .filter('terms', status=status_list)\

        query.aggs.metric('total_amount', 'sum',
                          field='total_unreceived_amount')
        results = query.execute()
        self_amount = results.aggregations.total_amount.value

        # Encumbrance of children accounts
        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        query.aggs.metric('total', 'sum', field='encumbrance_amount.total')
        results = query.execute()
        children_amount = results.aggregations.total.value

        return round(self_amount, 2), round(children_amount, 2)

    @property
    def expenditure_amount(self):
        """Get the expenditure amount related to this account.

        The expenditure amount is the sum of the amounts of receipt lines
        plus the sum of all receipt amount_adjustments related to this account.
        :return A tuple of expenditure amount : First element for self
                 expenditure amount, second element is the children
                 expenditure amount.
        """
        # Expenditure of this account
        search = AcqReceiptLinesSearch() \
            .filter('term', acq_account__pid=self.pid)
        search.aggs.metric('sum_receipt_lines', 'sum', field='total_amount')
        results = search.execute()
        lines_expenditure = results.aggregations.sum_receipt_lines.value

        receipt_expenditure = 0
        search = AcqReceiptsSearch() \
            .filter(
                'nested',
                path='amount_adjustments',
                query=Q(
                    'bool', must=[
                        Q('match',
                          amount_adjustments__acq_account__pid=self.pid)
                    ]
                )
            )
        for hit in search.scan():
            receipt_expenditure += sum([
                adjustment.amount for adjustment in hit.amount_adjustments
                if adjustment.acq_account.pid == self.pid
            ])
        self_amount = lines_expenditure + receipt_expenditure

        # Expenditure of children accounts
        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        query.aggs.metric('total', 'sum', field='expenditure_amount.total')
        results = query.execute()
        children_amount = round(results.aggregations.total.value, 2)
        return round(self_amount, 2), round(children_amount, 2)

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

        return round(self_balance, 2), round(total_balance, 2)

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
        return round(results.aggregations.total_amount.value, 2)

    def get_exceedance(self, exceed_type):
        """Compute the exceedance allowed for this account by type.

        :param exceed_type: the exceedance type to compute. Check
               `AcqAccountExceedanceType` class for values.
        :return the exceedance amount allowed rounded to the nearest centime.
        """
        rate = 0
        if exceed_type == AcqAccountExceedanceType.ENCUMBRANCE:
            rate = self.get('encumbrance_exceedance', 0)
        elif exceed_type == AcqAccountExceedanceType.EXPENDITURE:
            rate = self.get('expenditure_exceedance', 0)
        return round(self['allocated_amount'] * rate) / 100

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

    def get_ancestors(self):
        """Get all ancestors related to this account.

        :return a list of ancestor accounts.
        """
        if parent := self.parent:
            return [parent] + parent.get_ancestors()
        return []

    def get_children(self, output=None):
        """Get children accounts related to this account.

        :param output: output method. 'count' or None
        :return a generator of children accounts (or length).
        """
        query = AcqAccountsSearch().filter('term', parent__pid=self.pid)
        if output == 'count':
            return query.count()
        return get_objects(AcqAccount, query)

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        links = {}
        order_lines_query = AcqOrderLinesSearch()\
            .filter('term', acq_account__pid=self.pid)
        children_query = AcqAccountsSearch()\
            .filter('term', parent__pid=self.pid)
        invoices_query = AcquisitionInvoicesSearch()\
            .filter('term', invoice_items__acq_account__pid=self.pid)
        receipts_query = AcqReceiptsSearch()\
            .filter('nested',
                    path='amount_adjustments',
                    query=Q(
                        'bool',
                        must=[Q('match',
                                amount_adjustments__acq_account__pid=self.pid)]
                    ))

        if get_pids:
            order_lines = sorted_pids(order_lines_query)
            children = sorted_pids(children_query)
            invoices = sorted_pids(invoices_query)
            receipts = sorted_pids(receipts_query)
        else:
            order_lines = order_lines_query.count()
            children = children_query.count()
            invoices = invoices_query.count()
            receipts = receipts_query.count()

        if order_lines:
            links['acq_order_lines'] = order_lines
        if children:
            links['acq_accounts'] = children
        if invoices:
            links['acq_invoices'] = invoices
        if receipts:
            links['acq_receipts'] = receipts
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        # Note: not possible to delete records attached to rolled_over budget.
        if not self.is_active:
            cannot_delete['links'] = {'rolled_over': True}
            return cannot_delete
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        return cannot_delete


class AcqAccountsIndexer(IlsRecordsIndexer):
    """Indexing AcqAccount in Elasticsearch."""

    record_cls = AcqAccount

    def index(self, record):
        """Indexing an acq account record (and parent if needed)."""
        return_value = super().index(record)
        if parent_account := record.parent:
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
