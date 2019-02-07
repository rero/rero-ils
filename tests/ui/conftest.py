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

"""Common pytest fixtures and plugins."""


import pytest
from invenio_search import current_search_client

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patron_types.api import PatronType


@pytest.fixture(scope="function")
def tmp_organisation(db, organisation_data):
    """."""
    org = Organisation.create(
        data=organisation_data,
        dbcommit=True,
        delete_pid=True)
    return org


@pytest.fixture(scope="function")
def tmp_patron_type(db, patron_type_data):
    """."""
    org = PatronType.create(
        data=patron_type_data,
        dbcommit=True,
        delete_pid=True)
    return org


@pytest.fixture(scope='module')
def create_app():
    """Create test app."""
    # from invenio_app.factory import create_ui
    # create_ui
    from invenio_app.factory import create_ui

    return create_ui


@pytest.fixture()
def ils_record():
    """Ils Record test record."""
    yield {
        'pid': 'ilsrecord_pid',
        'name': 'IlsRecord Name',
    }


@pytest.fixture()
def ils_record_2():
    """Ils Record test record 2."""
    yield {
        'pid': 'ilsrecord_pid_2',
        'name': 'IlsRecord Name 2',
    }


@pytest.fixture(scope='module')
def es_default_index(es):
    """."""
    current_search_client.indices.create(
        index='records-record-v1.0.0',
        body={},
        ignore=[400]
    )
    yield es
    current_search_client.indices.delete(
        index='records-record-v1.0.0',
        ignore=[400, 404]
    )
