# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

# import pytest
from invenio_circulation.pidstore.fetchers import loan_pid_fetcher
from invenio_circulation.proxies import current_circulation
from utils import get_mapping

from rero_ils.modules.loans.api import Loan


def test_loans_create(db, loan_data_tmp):
    """Test loananisation creation."""
    loan = Loan.create(loan_data_tmp, delete_pid=True)
    assert loan == loan_data_tmp
    assert loan.get('loan_pid') == '1'
    assert loan.get('state') == 'PENDING'

    loan = Loan.get_record_by_pid('1')
    assert loan == loan_data_tmp

    fetched_pid = loan_pid_fetcher(loan.id, loan)
    assert fetched_pid.pid_value == '1'


def test_loan_es_mapping(es_clear, db, loan_data_tmp, item_lib_martigny,
                         loc_public_fully, lib_fully):
    """Test loans elasticsearch mapping."""
    search = current_circulation.loan_search
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)
