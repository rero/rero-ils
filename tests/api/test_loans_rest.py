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

# import json
# from utils import get_json, to_relative_url


from flask import url_for
from invenio_accounts.testutils import login_user_via_session


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
