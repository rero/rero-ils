# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

"""Operation log record extensions."""
import uuid
from datetime import datetime, timezone
from functools import partialmethod

import pytz
from deepdiff import DeepDiff
from flask import request as flask_request
from invenio_records.extensions import RecordExtension

from rero_ils.modules.patrons.api import current_librarian

from .models import OperationLogOperation
from ..utils import extracted_data_from_ref


class OperationLogObserverExtension(RecordExtension):
    """Observe a resource and build operation log when it changes."""

    def get_additional_informations(self, record):
        """Get some informations to add into the operation log.

        Subclasses can override this property to add some informations into
        the operation log dictionary.

        :param record: the observed record.
        :return a dict with additional informations.
        """
        return None

    def _build_operation_log(self, record, operation):
        """Build the operation log dict based on record.

        :param record: the updated record.
        :param operation: the trigger operation on this record.
        :return a dict representing the operation log to register.
        """
        oplg = {
            'date': datetime.now(timezone.utc).isoformat(),
            'record': {
                'value': record.get('pid'),
                'type': record.provider.pid_type
            },
            'operation': operation,
            'user_name': 'system'  # default value, could be override
        }
        if (
            hasattr(record, 'organisation_pid')
            and (org_pid := record.organisation_pid)
        ):
            oplg['record']['organisation_pid'] = org_pid
        if hasattr(record, 'library_pid') and (org_pid := record.library_pid):
            oplg['record']['library_pid'] = org_pid
        if current_librarian:
            oplg |= {
                'user_name': current_librarian.formatted_name,
                'user': {
                    'type': 'ptrn',
                    'value': current_librarian.pid
                },
                'organisation': {
                    'type': 'org',
                    'value': current_librarian.organisation_pid
                },
                'library': {
                    'type': 'lib',
                    'value': current_librarian.library_pid
                },
            }
            if (lib_pid := flask_request.args.get('current_library')) \
                    and lib_pid in current_librarian.manageable_library_pids:
                oplg |= {
                    'organisation': {
                        'type': 'org',
                        'value': current_librarian.organisation_pid
                    },
                    'library': {
                        'type': 'lib',
                        'value': lib_pid
                    }
                }

        # Allow additional informations for the operation log.
        #   Subclasses can override the ``additional_informations()`` method
        #   to add some data into the operation log dict
        oplg |= (self.get_additional_informations(record) or {})
        return oplg

    def _create_operation_log(self, record, operation, **kwargs):
        """Build and register an operation log."""
        from .api import OperationLog
        data = self._build_operation_log(record, operation)
        OperationLog.create(data)

    post_create = partialmethod(
        _create_operation_log,
        operation=OperationLogOperation.CREATE
    )
    """Called after a record is created."""

    pre_commit = partialmethod(
        _create_operation_log,
        operation=OperationLogOperation.UPDATE
    )
    """Called before a record is committed."""

    post_delete = partialmethod(
        _create_operation_log,
        operation=OperationLogOperation.DELETE
    )
    """Called after a record is deleted."""


class UntrackedFieldsOperationLogObserverExtension\
        (OperationLogObserverExtension):
    """Extension to skip Operation log if only some field changed.

    If you need to observe a resource but skip changes on some resource
    attributes, you can do it using this ``RecordExtension``. When you create
    the extension, you need to provide attributes that must be untracked (using
    the attribute xpath).

    Example:
       >> # OperationLog will be created except if 'status' attribute changed.
       >> _extensions=[
       >>    UntrackedFieldsOperationLogObserverExtension(['status'])
       >> ]

       >> # OperationLog will be created except if '$ref' attribute (from loan
       >> # attribute) changed.
       >> _extensions=[
       >>    UntrackedFieldsOperationLogObserverExtension(['loan.$ref'])
       >> ]
    """

    def __init__(self, fields=None):
        """Init."""
        if isinstance(fields, str):
            fields = [fields]
        self.exclude_path = [f"root['{f}']" for f in fields or []]

    def pre_commit(self, record):
        """Called before a record is committed."""
        original_record = record.__class__.get_record_by_pid(record.pid)
        diff = DeepDiff(
            original_record, record,
            verbose_level=2,
            exclude_paths=self.exclude_path
        )
        if diff:
            super().pre_commit(record)


class ResolveRefsExtension(RecordExtension):
    """Replace all $ref values by a dict of pid, type."""

    mod_type = {
        'documents': 'doc',
        'items': 'item',
        'holdings': 'hold',
        'loans': 'loan',
        'ill_requests': 'illr',
        'patrons': 'ptrn',
        'organisations': 'org',
        'libraries': 'lib'
    }

    def pre_dump(self, record, dumper=None):
        """Called before a record is dumped.

        :param record: the record metadata.
        :param dumper: the record dumper.
        """
        self._resolve_refs(record)

    def _resolve_refs(self, record):
        """Recursively replace the $refs.

        Replace in place all $ref to a dict of pid, type values.

        :param record: the record metadata.
        """
        for k, v in record.items():
            if isinstance(v, dict):
                if v.get('$ref'):
                    _type = self.mod_type.get(
                        extracted_data_from_ref(v, data='resource'))
                    if _type:
                        resolved = dict(
                            pid=extracted_data_from_ref(v),
                            type=_type
                        )
                        record[k] = resolved
                else:
                    self._resolve_refs(v)


class IDExtension(RecordExtension):
    """Generate an unique ID if does not exists."""

    def pre_create(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        if not record.get('pid'):
            record['pid'] = str(uuid.uuid1())


class DatesExtension(RecordExtension):
    """Set the created and updated date if needed."""

    def pre_create(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        iso_now = pytz.utc.localize(datetime.utcnow()).isoformat()
        for date_field in ['_created', '_updated']:
            if not record.get(date_field):
                record[date_field] = iso_now
