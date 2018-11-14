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

"""Pytest fixtures and plugins for the UI application."""

import pytest

from rero_ils.modules.patrons_types.api import PatronType
from rero_ils.utils_test import create_user


@pytest.fixture()
def user_staff_patron(app, minimal_patron_type_record):
    """Create staff patron user."""
    patron_type = PatronType.create(
        minimal_patron_type_record, dbcommit=True, reindex=True
    )
    yield create_user(
        app=app,
        name='staff_patron',
        is_patron=True,
        is_staff=True,
        patron_type_pid=patron_type.pid,
    )


@pytest.fixture()
def user_staff(app):
    """Create staff user."""
    yield create_user(app=app, name='staff', is_staff=True)


@pytest.fixture()
def user_patron(app, minimal_patron_type_record):
    """Create patron user."""
    patron_type = PatronType.create(
        minimal_patron_type_record, dbcommit=True, reindex=True
    )
    yield create_user(
        app=app, name='patron', is_patron=True, patron_type_pid=patron_type.pid
    )
