# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Add library_pid to ill_request operation logs."""
from logging import getLogger

from invenio_search.api import RecordsSearch

from rero_ils.modules.ill_requests.api import ILLRequest
from rero_ils.modules.loans.logs.api import LoanOperationLog
from rero_ils.modules.operation_logs.api import OperationLogsSearch

# revision identifiers, used by Alembic.
revision = '21a994dc2beb'
down_revision = '74ab9da9f078'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def upgrade():
    """Upgrade ill request operation logs records.

    For all ON_LOAN records, we will add a new `checkout_location_pid` field
    used to calculate fees based on checkout library.
    """
    query = RecordsSearch(index=LoanOperationLog.index_name)\
        .filter('term', record__type='illr')
    pids = [hit.pid for hit in query.source('pid').scan()]
    LOGGER.info(f'Upgrade operation logs illr :: {len(pids)}')
    errors = 0
    for idx, pid in enumerate(pids, 1):
        record = LoanOperationLog.get_record(pid)
        ill_request_pid = record['record']['value']
        if ill_request := ILLRequest.get_record_by_pid(ill_request_pid):
            record[
                'ill_request']['library_pid'] = ill_request.get_library().pid
            try:
                LoanOperationLog.update(pid, record['date'], record)
            except Exception as err:
                LOGGER.error(f'{idx:<10} {pid} {err}')
                errors += 1
        else:
            LOGGER.error(
                f'{idx:<10} {pid} ill request not found {ill_request_pid}')
            errors += 1
    OperationLogsSearch.flush_and_refresh()
    LOGGER.info(f'Changed: {idx} Errors: {errors}')


def downgrade():
    """Upgrade ill request operation logs records.

    For all ON_LOAN records, we will add a new `checkout_location_pid` field
    used to calculate fees based on checkout library.
    """
    query = RecordsSearch(index=LoanOperationLog.index_name)\
        .filter('term', record__type='illr')
    pids = [hit.pid for hit in query.source('pid').scan()]
    LOGGER.info(f'Downgrade operation logs illr :: {len(pids)}')
    errors = 0
    for idx, pid in enumerate(pids, 1):
        record = LoanOperationLog.get_record(pid)
        record['ill_request'].pop('library_pid', None)
        try:
            LoanOperationLog.update(pid, record['date'], record)
        except Exception as err:
            LOGGER.error(f'{idx:<10} {pid} {err}')
            errors += 1
    OperationLogsSearch.flush_and_refresh()
    LOGGER.info(f'Changed: {idx} Errors: {errors}')
