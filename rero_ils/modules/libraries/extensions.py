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

"""Invenio extensions for `Library` resources."""
from celery import current_app as celery_app
from deepdiff import DeepDiff
from invenio_cache import current_cache
from invenio_records.extensions import RecordExtension

from .tasks import calendar_changes_update_loans


class LibraryCalendarChangesExtension(RecordExtension):
    """Handle any changes on library calendar.

    When the library calendar changes, it could impact related active loans :
    If the loan ends now at a closed day/exception date, this loan end_date
    must be adapted to next_open_date.
    As it could potentially concern many loans, this operation can't be
    synchronously operated. So a detached Celery task will be called to execute
    changes.

    NOTE: If user operates multiple changes on library calendar in a small
          period of time, we need to ensure than only last detached task will
          be performed. So before running a new task, we MUST abort previously
          running task for the same library.
    """

    def __init__(self, tracked_fields):
        """Initialization method.

        :param tracked_fields: (list<String>) list of tracked fields.
        """
        if not isinstance(tracked_fields, list) or not tracked_fields:
            raise TypeError("'tracked_fields' is required")
        self._changes_detected = False
        self._tracked_fields = tracked_fields
        super().__init__()

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: the new record data.
        """
        db_record = record.db_record()
        for field_name in self._tracked_fields:
            original_field = db_record.get(field_name)
            new_field = record.get(field_name)
            if DeepDiff(original_field, new_field, ignore_order=True):
                self._changes_detected = True
                break

    def post_commit(self, record):
        """Called after a record is committed.

        :param record: the `Library` updated record
        """
        if self._changes_detected:
            self._changes_detected = False  # Reset changes detection
            task = calendar_changes_update_loans.s(record).apply_async()
            self._cache_current_task(record, task)

    @staticmethod
    def _cache_current_task(record, task):
        """Store the task_id into the application cache.

        :param record: the touched library record.
        :param task: the task related to the library.
        """
        content = current_cache.get('library-calendar-changes') or {}
        # If a previous task is still present into this cache entry, revoke it.
        # DEV NOTE : the task MUST clean (remove) this cache entry when task is
        #            finished.
        if task_id := content.pop(record.pid, None):
            celery_app.control.revoke(task_id, terminate=True)
        content[record.pid] = task.id
        current_cache.set('library-calendar-changes', content)
