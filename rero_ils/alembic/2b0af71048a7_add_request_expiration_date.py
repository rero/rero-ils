# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Loans :: Add request expiration field."""

from datetime import datetime, timedelta
from logging import getLogger

import ciso8601
import pytz
from elasticsearch_dsl import Q
from invenio_circulation.proxies import current_circulation

from rero_ils.modules.loans.api import Loan, LoansIndexer
from rero_ils.modules.loans.models import LoanState

# revision identifiers, used by Alembic.
revision = '2b0af71048a7'
down_revision = 'cc7ffbe1e078'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def upgrade():
    """Update loans records."""
    query = current_circulation.loan_search_cls() \
        .filter('term', state=LoanState.ITEM_AT_DESK) \
        .exclude('exists', field='request_expire_date') \
        .source('pid')
    loan_pids = [hit.pid for hit in query.scan()]
    ids = []
    for pid in loan_pids:
        loan = Loan.get_record_by_pid(pid)
        trans_date = ciso8601.parse_datetime(loan.transaction_date)
        expire_date = trans_date + timedelta(days=10)
        expire_date = expire_date.replace(
            hour=23, minute=59, second=00, microsecond=000,
            tzinfo=None)
        expire_date = pytz.timezone('Europe/Zurich').localize(expire_date)
        loan['request_expire_date'] = expire_date.isoformat()
        loan['request_start_date'] = datetime.now().isoformat()
        loan.update(loan, dbcommit=True, reindex=False)
        LOGGER.info(f'  * Updated loan#{loan.pid}')
        ids.append(loan.id)
    if len(ids):
        LOGGER.info(f'Indexing {len(ids)} records ....')
        indexer = LoansIndexer()
        indexer.bulk_index(ids)
        count = indexer.process_bulk_queue()
        LOGGER.info(f'{count} records indexed.')
    LOGGER.info(f'TOTAL :: {len(ids)}')


def downgrade():
    """Reset loans records."""
    # Nothing to do :: We can't remove the `request_expire_date` attribute
    # because the `CirculationDatesExtension` extension will always add a new
    # value during the record update
