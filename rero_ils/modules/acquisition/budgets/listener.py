# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Budgets."""

from rero_ils.modules.acquisition.acq_accounts.api import (
    AcqAccountsIndexer,
    AcqAccountsSearch,
)
from rero_ils.modules.acquisition.budgets.api import Budget
from rero_ils.modules.tasks import process_bulk_queue


def budget_is_active_changed(sender, record=None, *args, **kwargs):
    """Reindex related account if is_active field changes."""
    if isinstance(record, Budget):
        ori_record = Budget.get_record_by_pid(record.pid)
        if ori_record["is_active"] != record["is_active"]:
            search = AcqAccountsSearch().filter("term", budget__pid=record.pid).source().scan()
            uuids = [hit.meta.id for hit in search]
            AcqAccountsIndexer().bulk_index(uuids)
            process_bulk_queue.apply_async()
