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

import mock
import pytest
from utils import flush_index

from rero_ils.modules.patrons.api import Patron, PatronsSearch


@pytest.fixture(scope="module")
def sip2_librarian_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(data.get('ptrn2'))


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def sip2_librarian_martigny_no_email(
        app,
        roles,
        lib_martigny,
        sip2_librarian_martigny_data):
    """Create Martigny librarian without sending reset password instruction."""
    # create patron account
    patron = Patron.create(
        data=sip2_librarian_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)

    flush_index(PatronsSearch.Meta.index)
    return patron


@pytest.fixture(scope="module")
def sip2_patron_martigny_data(data):
    """Load Martigny librarian data."""
    return deepcopy(data.get('ptrn6'))


@pytest.fixture(scope="module")
@mock.patch('rero_ils.modules.patrons.api.send_reset_password_instructions')
def sip2_patron_martigny_no_email(
        app,
        roles,
        patron_type_children_martigny,
        sip2_patron_martigny_data):
    """Create Martigny patron without sending reset password instruction."""
    # create patron account
    patron = Patron.create(
        data=sip2_patron_martigny_data,
        delete_pid=False,
        dbcommit=True,
        reindex=True)

    flush_index(PatronsSearch.Meta.index)
    return patron
