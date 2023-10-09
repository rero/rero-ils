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

"""Common pytest fixtures and plugins for SIP2."""

from copy import deepcopy

import pytest
from utils import create_patron, create_selfcheck_terminal, \
    create_user_token, patch_expiration_date


@pytest.fixture(scope="module")
def selfcheck_librarian_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(patch_expiration_date(data.get('ptrn2')))


@pytest.fixture(scope="module")
def selfcheck_librarian_martigny(app, roles, loc_public_martigny,
                                 librarian_martigny,
                                 selfcheck_termial_martigny_data):
    """Create selfcheck config and token for Martigny librarian."""
    # create token for selfcheck terminal
    create_user_token(
        client_name='selfcheck_token',
        user=librarian_martigny.user,
        access_token=selfcheck_termial_martigny_data.get('access_token')
    )

    # create config for selfcheck terminal
    data = selfcheck_termial_martigny_data
    return create_selfcheck_terminal(data)


@pytest.fixture(scope="module")
def selfcheck_termial_martigny_data(data):
    """Load Martigny librarian SIP2 account data."""
    return {
        'name': 'sip2Test',
        'access_token': 'TESTACCESSTOKEN',
        'organisation_pid': 'org1',
        'library_pid': 'lib1',
        'location_pid': 'loc1',
    }


@pytest.fixture(scope="module")
def selfcheck_patron_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(patch_expiration_date(data.get('ptrn6')))


@pytest.fixture(scope="module")
def selfcheck_patron_martigny(app, roles, lib_martigny,
                              patron_type_children_martigny,
                              selfcheck_patron_martigny_data):
    """Create Martigny patron without sending reset password instruction."""
    # create patron account
    data = selfcheck_patron_martigny_data
    yield create_patron(data)
