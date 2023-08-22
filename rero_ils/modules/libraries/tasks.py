# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Tasks on `Library` resource."""
import contextlib

from celery import shared_task
from invenio_cache import current_cache

from .exceptions import LibraryNeverOpen


@shared_task(name='library-calendar-changes-update-loans')
def calendar_changes_update_loans(record_data):
    """Task to update related loans if library calendar changes.

    If a library calendar changes, we will ensure that pending loans end_dates
    are still coherent with this calendar. If the end_date is now detected as
    a closed library date, the end_date of the loan will be updated to the
    next opening day of the library.

    ..notes..
       we only check about 'closed date' changes into the library calendar. In
       case of new opening day/date is set, pending loan end_date shouldn't be
       "down dated" (it will cause more problems with possible already sent
       notification).
       Example :
        * Patron receive a notification at Monday telling that
          the return date is Wednesday (because Tuesday is closed).
        * Next we edit the calendar to set all tuesday as opening day. In this
          use case the loan end_date will set to "Tuesday" (or maybe is already
          overdue if the loan is for multiple weeks).
        * Patron checkouts the book on Wednesday (as mentioned in received
          notification) but a fee will be possibly created.

    :param record_data: Data representing the library to check.
    """

    def _at_finish():
        """Inner method called when the task finished."""
        # DEV NOTES :: Clean the cache to remove task_id when finished
        #   We build a behavior ot avoid multiple concurrent similar tasks at
        #   same time. The parent process running the task should place a stamp
        #   when the task is registered. So, to specify another similar task
        #   must be started without collision, we need to clean this stamp.
        # DEV NOTES :: Why not using 'decorator'
        #   A better way should be to use `@clean_cache` decorator ; this
        #   decorator should take the key to clean as argument. But we didn't
        #   know the key because it's created from `record_data`. This is why
        #   it's easier to create a small specific function.
        cache_content = current_cache.get('library-calendar-changes') or {}
        cache_content.pop(library.pid, {})
        current_cache.set('library-calendar-changes', cache_content)

    from rero_ils.modules.loans.api import LoansIndexer, \
        get_on_loan_loans_for_library

    from .api import Library

    library = Library(record_data)
    active_loan_counter = 0
    changed_loan_uuids = []
    for loan in get_on_loan_loans_for_library(library.pid):
        active_loan_counter += 1
        if not library.is_open(loan.end_date):
            with contextlib.suppress(LibraryNeverOpen):
                loan['end_date'] = library \
                    .next_open(loan.end_date) \
                    .astimezone(library.get_timezone()) \
                    .replace(hour=23, minute=59, second=0, microsecond=0)\
                    .isoformat()
                changed_loan_uuids.append(loan.id)
                loan.update(loan, dbcommit=True, reindex=False)
    indexer = LoansIndexer()
    indexer.bulk_index(changed_loan_uuids)
    indexer.process_bulk_queue()

    _at_finish()
    return active_loan_counter, len(changed_loan_uuids)
