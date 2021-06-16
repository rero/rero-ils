# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Signals connector for Operation log."""

from datetime import datetime, timezone

from flask import current_app

from .api import OperationLog
from ..patrons.api import current_librarian
from ..utils import extracted_data_from_ref


def operation_log_record_create(sender, record=None, *args, **kwargs):
    """Create an operation log entry after record creation.

    Checks if the record is configured to keep logs of its creation.
    If enabled, a new operation log entry will be added. Method is called after
    record creation by connecting to signals'after_record_insert'.

    :param record: the record being created.
    """
    build_operation_log_record(record=record, operation='create')


def operation_log_record_update(sender, record=None, *args, **kwargs):
    """Create an operation log entry after record update.

    Checks if the record is configured to keep logs of its update.
    If enabled, a new operation log entry will be added. Method is called after
    record update by connecting to the 'after_record_update' signal.

    :param record: the record being updated.
    """
    build_operation_log_record(record=record, operation='update')


def operation_log_record_delete(sender, record=None, *args, **kwargs):
    """Create an operation log entry after record deletion.

    Checks if the record is configured to keep logs of its deletion.
    If enabled, a new operation log entry will be added. Method is called after
    record deletion by connecting to signals'after_record_delete'.

    :param record: the record being created.
    """
    build_operation_log_record(record=record, operation='delete')


def build_operation_log_record(record=None, operation=None):
    """Build an operation_log record to load.

    :param record: the record being created.
    """
    if record.get('$schema'):
        resource_name = extracted_data_from_ref(
            record.get('$schema'), data='resource')
        if resource_name in current_app.config.get(
                'RERO_ILS_ENABLE_OPERATION_LOG'):
            oplg = {
                'date': datetime.now(timezone.utc).isoformat(),
                'record': {
                    'value': record.get('pid'),
                    'type': record.provider.pid_type
                },
                'operation': operation
            }
            if resource_name == 'ill_requests':
                oplg['ill_request'] = {
                    'status': record.get('status'),
                }
                loan_status = record.get('loan_status')
                if loan_status:
                    oplg['ill_request']['loan_status'] = loan_status

            if current_librarian:
                oplg['user'] = {
                    'type': 'ptrn',
                    'value': current_librarian.pid
                }
                oplg['user_name'] = current_librarian.formatted_name
                oplg['organisation'] = {
                    'value': current_librarian.organisation_pid,
                    'type': 'org'
                }
                oplg['library'] = {
                    'value': current_librarian.library_pid,
                    'type': 'lib'
                }
            else:
                oplg['user_name'] = 'system'
            OperationLog.create(oplg)
