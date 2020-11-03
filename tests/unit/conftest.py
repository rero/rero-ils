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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import pytest
from pkg_resources import resource_string
from utils import get_schema


@pytest.fixture(scope='module')
def create_app():
    """Create test app."""
    from invenio_app.factory import create_ui
    return create_ui


@pytest.fixture()
def circ_policy_schema(monkeypatch):
    """Circ policy Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.circ_policies.jsonschemas',
        'circ_policies/circ_policy-v0.0.1.json',
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def template_schema(monkeypatch):
    """Template Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.templates.jsonschemas',
        'templates/template-v0.0.1.json',
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def notification_schema(monkeypatch):
    """Notifications Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.notifications.jsonschemas',
        '/notifications/notification-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def item_type_schema(monkeypatch):
    """Item type Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.item_types.jsonschemas',
        '/item_types/item_type-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def acq_account_schema(monkeypatch):
    """Acq account Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.acq_accounts.jsonschemas',
        '/acq_accounts/acq_account-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def budget_schema(monkeypatch):
    """Budget Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.budgets.jsonschemas',
        '/budgets/budget-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def library_schema(monkeypatch):
    """Library Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.libraries.jsonschemas',
        'libraries/library-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def location_schema(monkeypatch):
    """Location Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.locations.jsonschemas',
        'locations/location-v0.0.1.json')
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def patron_transaction_schema(monkeypatch):
    """Patron transaction Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.patron_transactions.jsonschemas',
        'patron_transactions/patron_transaction-v0.0.1.json')
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def patron_transaction_event_schema(monkeypatch):
    """Patron transaction event Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.patron_transaction_events.jsonschemas',
        'patron_transaction_events/patron_transaction_event-v0.0.1.json')
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def organisation_schema(monkeypatch):
    """Organisation Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.organisations.jsonschemas',
        'organisations/organisation-v0.0.1.json',
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def patron_type_schema(monkeypatch):
    """Patron type Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.patron_types.jsonschemas',
        '/patron_types/patron_type-v0.0.1.json',
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def patron_schema(monkeypatch):
    """Patron Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.patrons.jsonschemas',
        '/patrons/patron-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture(scope="function")
def patron_martigny_data_tmp_with_id(patron_martigny_data_tmp):
    """Load Martigny patron data scope function with a mocked user_id."""
    patron = deepcopy(patron_martigny_data_tmp)
    # mock the user_id which is add by the Patron API.
    patron['user_id'] = 100
    return patron


@pytest.fixture()
def persons_schema(monkeypatch):
    """Patron Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.persons.jsonschemas',
        '/persons/person-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def document_schema(monkeypatch):
    """Jsonschema for documents."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.documents.jsonschemas',
        'documents/document-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def item_schema(monkeypatch):
    """Item Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.items.jsonschemas',
        'items/item-v0.0.1.json'
    )
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def holding_schema(monkeypatch):
    """Holdings Jsonschema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.holdings.jsonschemas',
        '/holdings/holding-v0.0.1.json')
    return get_schema(monkeypatch, schema_in_bytes)


@pytest.fixture()
def ill_request_schema(monkeypatch):
    """ILL requests JSONSchema for records."""
    schema_in_bytes = resource_string(
        'rero_ils.modules.ill_requests.jsonschemas',
        '/ill_requests/ill_request-v0.0.1.json')
    return get_schema(monkeypatch, schema_in_bytes)
