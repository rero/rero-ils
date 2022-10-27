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

"""Signals connector for Acquisition account."""
from .api import AcqAccount, AcqAccountsSearch
from .models import AcqAccountExceedanceType


def enrich_acq_account_data(sender, json=None, record=None, index=None,
                            doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == AcqAccountsSearch.Meta.index:
        account = record
        if not isinstance(record, AcqAccount):
            account = AcqAccount.get_record_by_pid(record.get('pid'))

        # compute the exceedance amounts
        amount = account.get('allocated_amount', 0)
        if amount:
            if 'encumbrance_exceedance' in account:
                json['encumbrance_exceedance'] = dict(
                    value=account.get('encumbrance_exceedance'),
                    amount=account.get_exceedance(
                        AcqAccountExceedanceType.ENCUMBRANCE)
                )
            if 'expenditure_exceedance' in account:
                json['expenditure_exceedance'] = dict(
                    value=account.get('expenditure_exceedance'),
                    amount=account.get_exceedance(
                        AcqAccountExceedanceType.EXPENDITURE)
                )
        else:
            json.pop('encumbrance_exceedance', None)
            json.pop('expenditure_exceedance', None)

        # encumbrance, expenditure and balance amounts
        (self_amount, children_amount) = account.encumbrance_amount
        json['encumbrance_amount'] = dict(
            self=self_amount,
            children=children_amount,
            total=self_amount + children_amount
        )
        (self_amount, children_amount) = account.expenditure_amount
        json['expenditure_amount'] = dict(
            self=self_amount,
            children=children_amount,
            total=self_amount + children_amount
        )
        (self_amount, total_amount) = account.remaining_balance
        json['remaining_balance'] = dict(
            self=self_amount,
            total=total_amount
        )

        # additional fields for ES
        json['is_active'] = account.is_active
        json['depth'] = account.depth
        json['distribution'] = account.distribution
        json['organisation'] = dict(
            pid=account.organisation_pid,
            type='org'
        )
