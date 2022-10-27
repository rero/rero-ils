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

"""Signals connector for Budgets."""

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccountsIndexer, \
    AcqAccountsSearch
from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.tasks import process_bulk_queue


def budget_is_active_changed(sender, record=None, *args, **kwargs):
    """Reindex related account if is_active field changes."""
    if isinstance(record, Budget):
        ori_record = Budget.get_record_by_pid(record.pid)
        if ori_record['is_active'] != record['is_active']:
            # the `is_active` flag changed, we need to reindex all accounts
            # related to this budget
            uuids = []
            search = AcqAccountsSearch()\
                .filter('term', budget__pid=record.pid)\
                .source().scan()
            for hit in search:
                uuids.append(hit.meta.id)
            AcqAccountsIndexer().bulk_index(uuids)
            process_bulk_queue.apply_async()
