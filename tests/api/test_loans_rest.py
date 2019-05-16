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

"""Tests REST API item_types."""

from copy import deepcopy

import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.errors import CirculationException

from rero_ils.modules.loans.api import get_last_transaction_loc_for_item, \
    get_loans_by_patron_pid
from rero_ils.modules.loans.utils import can_be_requested


def test_loans_permissions(client, loan_pending, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loanid_item', pid_value='1')
    post_url = url_for('invenio_records_rest.loanid_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.loanid_item', pid_value='1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_loans_logged_permissions(client, loan_pending,
                                  librarian_martigny_no_email,
                                  json_header):
    """Test record retrieval."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item_url = url_for('invenio_records_rest.loanid_item', pid_value='1')
    post_url = url_for('invenio_records_rest.loanid_list')

    res = client.get(item_url)
    assert res.status_code == 403

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 403

    res = client.put(
        url_for('invenio_records_rest.loanid_item', pid_value='1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 403


def test_loan_utils(client, librarian_martigny_no_email, lib_martigny,
                    patron_martigny_no_email, item_lib_martigny,
                    item_type_standard_martigny,
                    patron_type_children_martigny,
                    circulation_policies, loan_pending,
                    librarian_martigny):
    """Test loan utils."""
    loan = {
        'item_pid': item_lib_martigny.pid,
        'patron_pid': patron_martigny_no_email.pid
    }
    assert can_be_requested(loan)

    del loan['item_pid']
    with pytest.raises(Exception):
        assert can_be_requested(loan)

    assert loan_pending.patron_pid == librarian_martigny.pid
    assert not loan_pending.is_active

    with pytest.raises(TypeError):
        assert get_loans_by_patron_pid()

    with pytest.raises(TypeError):
        assert get_last_transaction_loc_for_item()

    assert loan_pending.organisation_pid

    new_loan = deepcopy(loan_pending)
    assert new_loan.organisation_pid
    del new_loan['item_pid']
    assert not new_loan.organisation_pid
