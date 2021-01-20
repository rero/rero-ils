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
from ..patrons.api import current_patron
from ..utils import extracted_data_from_ref, get_ref_for_pid


def create_operation_log_record(sender, record=None, *args, **kwargs):
    """Create an operation log entry after record creation and update.

    Checks if the record is configured to keep logs of its creation and update.
    If enabled, a new operation log entry will be added. Method is called after
    record creation or update by connecting to signals'after_record_insert'
    and 'after_record_update'.

    :param record: the record being created.
    """
    if record.get('$schema'):
        resource_name = extracted_data_from_ref(
            record.get('$schema'), data='resource')
        if resource_name in current_app.config.get(
            'RERO_ILS_ENABLE_OPERATION_LOG'):
            oplg = {
                'date': datetime.now(timezone.utc).isoformat(),
                'record': {'$ref': get_ref_for_pid(
                    record.provider.pid_type, record.get('pid'))},
                'operation': 'create'
            }
            if current_patron:
                oplg['user'] = {
                    '$ref': get_ref_for_pid('ptrn', current_patron.pid)}
                oplg['user_name'] = current_patron.formatted_name
                oplg['organisation'] = {
                    '$ref': get_ref_for_pid('org', current_patron.organisation_pid)}
            else:
                oplg['user_name'] = 'system'
            OperationLog.create(oplg)
