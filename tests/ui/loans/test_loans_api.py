# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import timedelta

from invenio_circulation.proxies import current_circulation
from utils import get_mapping

from rero_ils.modules.loans.api import get_loans_by_patron_pid
from rero_ils.modules.loans.utils import get_default_loan_duration


def test_loan_es_mapping(es_clear, db):
    """Test loans elasticsearch mapping."""
    search = current_circulation.loan_search_cls
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)


def test_loans_create(loan_pending_martigny):
    """Test loan creation."""
    assert loan_pending_martigny.get('state') == 'PENDING'


def test_item_loans_elements(
        loan_pending_martigny, item_lib_fully, circ_policy_default_martigny):
    """Test loan elements."""
    assert loan_pending_martigny.item_pid == item_lib_fully.pid
    loan = list(get_loans_by_patron_pid(loan_pending_martigny.patron_pid))[0]
    assert loan.pid == loan_pending_martigny.get('pid')

    new_loan = deepcopy(loan_pending_martigny)
    del new_loan['transaction_location_pid']
    assert get_default_loan_duration(new_loan) == \
        get_default_loan_duration(loan_pending_martigny)

    assert item_lib_fully.last_location_pid == item_lib_fully.location_pid
    circ_policy_default_martigny['allow_checkout'] = False
    circ_policy_default_martigny.update(
        circ_policy_default_martigny, dbcommit=True, reindex=True)

    assert get_default_loan_duration(new_loan) == timedelta(0)
