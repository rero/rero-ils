# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Tests resource streamed exports."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_csv, parse_csv


def test_loans_exports(app, client, librarian_martigny,
                       loan_pending_martigny, loan2_validated_martigny):
    """Test loans streamed exportation."""
    # STEP#1 :: CHECK EXPORT PERMISSION
    #   Only authenticated user could export loans.
    url = url_for('api_exports.loan_export')
    res = client.get(url)
    assert res.status_code == 401

    # STEP#2 :: CHECK EXPORT RESOURCES
    #   Logged as librarian and test the export endpoint.
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url)
    assert res.status_code == 200
    data = list(parse_csv(get_csv(res)))

    header = data[0]
    header_columns = [
        'pid', 'document_title', 'item_barcode', 'item_call_numbers',
        'patron_name', 'patron_barcode', 'patron_email', 'patron_type',
        'owning_library', 'transaction_library', 'pickup_library',
        'state', 'end_date', 'request_expire_date'
    ]
    assert all(field in header for field in header_columns)
    assert len(data) == 3
