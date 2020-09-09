# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

"""Tests Selfcheck api."""

from __future__ import absolute_import, print_function

import pytest
from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import LoanAction
from rero_ils.modules.selfcheck.api import authorize_patron, enable_patron, \
    patron_information, selfcheck_login, system_status, \
    validate_patron_account
from rero_ils.modules.selfcheck.utils import check_sip2_module

# skip tests if invenio-sip2 module is not installed
pytestmark = pytest.mark.skipif(not check_sip2_module(),
                                reason='invenio-sip2 not installed')


def test_invenio_sip2():
    """Test invenio-sip2 module install."""
    assert check_sip2_module()


def test_selfcheck_login(sip2_librarian_martigny_no_email):
    """Test selfcheck client login."""

    # test failed login
    response = selfcheck_login('invalid_user',
                               'invalid_password')
    assert not response

    # test success login
    response = selfcheck_login(
        sip2_librarian_martigny_no_email.get('email'),
        sip2_librarian_martigny_no_email.get('birth_date'))
    assert response
    assert response.get('authenticated')


def test_authorize_patron(sip2_patron_martigny_no_email):
    """Test authorize patron."""

    # authorize failed login
    response = authorize_patron(sip2_patron_martigny_no_email.get('barcode'),
                                'invalid_password')
    assert not response

    # authorize success
    response = authorize_patron(
        sip2_patron_martigny_no_email.get('barcode'),
        sip2_patron_martigny_no_email.get('birth_date'))
    assert response


def test_validate_patron(patron_martigny):
    """Test validate patron."""
    # test valid patron barcode
    assert validate_patron_account(patron_martigny.get('barcode'))

    # test invalid patron barcode
    assert not validate_patron_account('invalid_barcode')


def test_system_status(sip2_librarian_martigny_no_email):
    """Test automated circulation system status."""
    response = system_status(sip2_librarian_martigny_no_email.get('email'))
    assert response.get('institution_id') == 'org1'


def test_enable_patron(sip2_patron_martigny_no_email):
    """Test enable patron."""
    response = enable_patron(sip2_patron_martigny_no_email.get('barcode'))
    assert response['institution_id'] == sip2_patron_martigny_no_email\
        .organisation_pid
    assert response['patron_id']
    assert response['patron_name']


def test_patron_information(client, sip2_librarian_martigny_no_email,
                            sip2_patron_martigny_no_email, loc_public_martigny,
                            item_lib_martigny, json_header,
                            circulation_policies):
    """Test patron information."""

    login_user_via_session(client, sip2_librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=sip2_patron_martigny_no_email.pid,
            transaction_user_pid=sip2_librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')

    response = patron_information(sip2_patron_martigny_no_email.get('barcode'))
    assert response
