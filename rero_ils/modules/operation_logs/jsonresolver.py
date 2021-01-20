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

"""OperationLog resolver."""

import jsonresolver
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


@jsonresolver.route('/api/operation_logs/<pid>', host='ils.rero.ch')
def operation_log_resolver(pid):
    """Resolver for operation_log record."""
    persist_id = PersistentIdentifier.get('oplg', pid)
    if persist_id.status == PIDStatus.REGISTERED:
        return dict(pid=persist_id.pid_value)
    current_app.logger.error(
        'Operation logs resolver error: /api/operation_logs/{pid} {persist_id}'
        .format(pid=pid, persistent_id=persist_id)
    )
    raise Exception('unable to resolve')
