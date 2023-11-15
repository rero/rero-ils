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

"""API for manipulating patron types."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q
from flask_babel import gettext as _

from .models import PatronTypeIdentifier, PatronTypeMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..circ_policies.api import CircPoliciesSearch
from ..fetchers import id_fetcher
from ..loans.api import get_loans_count_by_library_for_patron_pid, \
    get_overdue_loan_pids
from ..loans.models import LoanState
from ..minters import id_minter
from ..patron_transactions.utils import \
    get_transactions_total_amount_for_patron
from ..patrons.api import Patron, PatronsSearch
from ..providers import Provider
from ..utils import get_patron_from_arguments, sorted_pids

# provider
PatronTypeProvider = type(
    'PatronTypeProvider',
    (Provider,),
    dict(identifier=PatronTypeIdentifier, pid_type='ptty')
)
# minter
patron_type_id_minter = partial(id_minter, provider=PatronTypeProvider)
# fetcher
patron_type_id_fetcher = partial(id_fetcher, provider=PatronTypeProvider)


class PatronTypesSearch(IlsRecordsSearch):
    """PatronTypeSearch."""

    class Meta:
        """Search only on patrons index."""

        index = 'patron_types'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None

    def by_organisation_pid(self, organisation_pid):
        """Build a search to get hits related to an organisation pid.

        :param organisation_pid: string - the organisation pid to filter with
        :returns: An ElasticSearch query to get hits related the entity.
        :rtype: `elasticsearch_dsl.Search`
        """
        return self.filter('term', organisation__pid=organisation_pid)


class PatronType(IlsRecord):
    """PatronType class."""

    minter = patron_type_id_minter
    fetcher = patron_type_id_fetcher
    provider = PatronTypeProvider
    model_cls = PatronTypeMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation',
        }
    }

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensure than checkout limits are coherent.
        Ensure than library limit exceptions are coherent.

        """
        # validate checkout limits
        checkout_limits_data = self.get('limits', {}).get('checkout_limits')
        if checkout_limits_data:
            global_limit = checkout_limits_data.get('global_limit')
            library_limit = checkout_limits_data.get('library_limit')
            if library_limit:
                # Library limit cannot be higher than global limit
                if library_limit > global_limit:
                    return _('Library limit cannot be higher than global '
                             'limit.')
                # Exception limit cannot have same value than library limit
                # Only one exception per library
                exceptions_lib = []
                exceptions = checkout_limits_data.get('library_exceptions', [])
                for exception in exceptions:
                    if exception.get('value') == library_limit:
                        return _('Exception limit cannot have same value than '
                                 'library limit')
                    ref = exception.get('library').get('$ref')
                    if ref in exceptions_lib:
                        return _('Only one specific limit by library if '
                                 'allowed.')
                    exceptions_lib.append(ref)
        return True

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique within organisation."""
        patron_type = PatronTypesSearch()\
            .filter('term', patron_type_name=name)\
            .filter('term', organisation__pid=organisation_pid).source().scan()
        try:
            return next(patron_type)
        except StopIteration:
            return None

    @classmethod
    def get_yearly_subscription_patron_types(cls):
        """Get PatronType with an active yearly subscription."""
        results = PatronTypesSearch()\
            .filter('range', subscription_amount={'gt': 0})\
            .source('pid')\
            .scan()
        for result in results:
            yield cls.get_record_by_pid(result.pid)

    @classmethod
    def can_checkout(cls, item, **kwargs):
        """Check if a patron type allow checkout loan operation.

        :param item : the item to check
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # 'patron' argument are present into kwargs. This check can't
            # be relevant --> return True by default
            return True, []

        # check overdue items limits
        patron_type = PatronType.get_record_by_pid(patron.patron_type_pid)
        if not patron_type.check_overdue_items_limit(patron):
            return False, [_('Checkout denied: the maximal number of overdue '
                             'items is reached')]
        # check checkout count limit
        valid, message = patron_type.check_checkout_count_limit(patron, item)
        if not valid:
            return False, [message]
        # check fee amount limit
        if not patron_type.check_fee_amount_limit(patron):
            return False, [_('Checkout denied: the maximal overdue fee amount '
                             'is reached')]
        # check unpaid subscription
        if not patron_type.check_unpaid_subscription(patron):
            return False, \
                   [_('Checkout denied: patron has unpaid subscription')]
        return True, []

    @classmethod
    def can_request(cls, item, **kwargs):
        """Check if a patron type allow request item operation.

        :param item : the item to check
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # 'patron' argument are present into kwargs. This check can't
            # be relevant --> return True by default
            return True, []
        # check overdue items limits
        patron_type = PatronType.get_record_by_pid(patron.patron_type_pid)
        if not patron_type.check_overdue_items_limit(patron):
            return False, [_('Request denied: the maximal number of overdue '
                             'items is reached')]
        # check fee amount limit
        if not patron_type.check_fee_amount_limit(patron):
            return False, [_('Request denied: the maximal overdue fee amount '
                             'is reached')]
        # check unpaid subscription
        if not patron_type.check_unpaid_subscription(patron):
            return False, [_('Request denied: patron has unpaid subscription')]

        return True, []

    @classmethod
    def can_extend(cls, item, **kwargs):
        """Check if a patron type allow extend loan operation.

        :param item : the item to check
        :param kwargs : To be relevant, additional arguments should contains
                        'patron' argument.
        :return a tuple with True|False and reasons to disallow if False.
        """
        patron = get_patron_from_arguments(**kwargs)
        if not patron:
            # 'patron' argument are present into kwargs. This check can't
            # be relevant --> return True by default
            return True, []
        # check overdue items limit
        patron_type = PatronType.get_record_by_pid(patron.patron_type_pid)
        if not patron_type.check_overdue_items_limit(patron):
            return False, [_('Renewal denied: the maximal number of overdue '
                             'items is reached')]
        # check fee amount limit
        if not patron_type.check_fee_amount_limit(patron):
            return False, [_('Renewal denied: the maximal overdue fee amount '
                             'is reached')]
        # check unpaid subscription
        if not patron_type.check_unpaid_subscription(patron):
            return False, [_('Renewal denied: patron has unpaid subscription')]
        return True, []

    def get_linked_patron(self):
        """Get patron linked to this patron type."""
        results = PatronsSearch()\
            .filter('term', patron__type__pid=self.pid).source('pid').scan()
        for result in results:
            yield Patron.get_record_by_pid(result.pid)

    @property
    def is_subscription_required(self):
        """Check if a subscription is required for this patron type."""
        return self.get('subscription_amount', 0) > 0

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        ptrn_query = PatronsSearch()\
            .filter('term', patron__type__pid=self.pid)
        cipo_query = CircPoliciesSearch()\
            .filter(
                'nested',
                path='settings',
                query=Q(
                    'bool',
                    must=[Q('match', settings__patron_type__pid=self.pid)]
                )
            )
        links = {}
        if get_pids:
            patrons = sorted_pids(ptrn_query)
            circ_policies = sorted_pids(cipo_query)
        else:
            patrons = ptrn_query.count()
            circ_policies = cipo_query.count()
        if patrons:
            links['patrons'] = patrons
        if circ_policies:
            links['circ_policies'] = circ_policies
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    # CHECK LIMITS METHODS ====================================================
    def check_overdue_items_limit(self, patron):
        """Check if a patron reached the overdue items limit.

        :param patron: the patron who tries to execute the checkout.
        :return False if patron has more overdue items than defined limit. True
                in all other cases.
        """
        limit = self.get('limits', {}).get('overdue_items_limits', {})\
            .get('default_value')
        if limit:
            overdue_items = list(get_overdue_loan_pids(patron.pid))
            return limit > len(overdue_items)
        return True

    def check_checkout_count_limit(self, patron, item=None):
        """Check if a patron reached the checkout limits.

        * check the global general limit (if exists).
        * check the library exception limit (if exists).
        * check the library default limit (if exists).
        :param patron: the patron who tries to execute the checkout.
        :param item: the item related to the loan (optionnal).
        :return a tuple of two values ::
          - True|False : to know if the check is success or not.
          - message(string) : the reason why the check fails.
        """
        checkout_limits = self.replace_refs().get('limits', {})\
            .get('checkout_limits', {})
        global_limit = checkout_limits.get('global_limit')
        if not global_limit:
            return True, None

        # [0] get the stats for this patron by library
        patron_library_stats = get_loans_count_by_library_for_patron_pid(
            patron.pid, [LoanState.ITEM_ON_LOAN])

        # [1] check the general limit
        patron_total_count = sum(patron_library_stats.values()) or 0
        if patron_total_count >= global_limit:
            return False, _('Checkout denied: the maximal checkout number '
                            'is reached.')

        # [3] check library_limit if item is not none
        if item:
            item_lib_pid = item.library_pid
            library_limit_value = checkout_limits.get('library_limit')
            # try to find an exception rule for this library
            for exception in checkout_limits.get('library_exceptions', []):
                if exception['library']['pid'] == item_lib_pid:
                    library_limit_value = exception['value']
                    break
            if (
                library_limit_value
                and item_lib_pid in patron_library_stats
                and patron_library_stats[item_lib_pid] >= library_limit_value
            ):
                return False, _('Checkout denied: the maximal checkout '
                                'number of items for this library is '
                                'reached.')

        # [4] no problem detected, checkout is allowed
        return True, None

    def check_fee_amount_limit(self, patron):
        """Check if a patron reached the fee amount limits.

        * check the fee amount limit (if exists).
        :param patron: the patron who tries to execute the checkout.
        :return boolean to know if the check is success or not.
        """
        # get fee amount limit
        fee_amount_limits = self.replace_refs().get('limits', {}) \
            .get('fee_amount_limits', {})
        default_limit = fee_amount_limits.get('default_value')
        if default_limit:
            # get total amount for open transactions on overdue and without
            # subscription fee
            patron_total_amount = get_transactions_total_amount_for_patron(
                    patron.pid, status='open', types=['overdue'],
                    with_subscription=False)
            return patron_total_amount < default_limit
        return True

    def check_unpaid_subscription(self, patron):
        """Check if a patron as unpaid subscriptions.

        The 'unpaid_subscription' limit should be enable to have a consistent
        check.
        :param patron: the patron who tried to execute a circulation operation.
        :return boolean to know if the check is success or not.
        """
        unpaid_subscription_limit = self.get('limits', {})\
            .get('unpaid_subscription', True)
        if not unpaid_subscription_limit:
            return True, None
        unpaid_amount = get_transactions_total_amount_for_patron(
                patron.pid, status='open', types=['subscription'],
                with_subscription=True)
        return unpaid_amount == 0


class PatronTypesIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = PatronType

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='ptty')
