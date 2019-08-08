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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Common pytest fixtures and plugins."""


import pytest
from invenio_search import current_search, current_search_client

from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patron_types.api import PatronType


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
    """ES default index."""
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
