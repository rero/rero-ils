# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Statistics configuration JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(stats_cfg_schema):
    """Test required for template jsonschema."""

    with pytest.raises(ValidationError):
        validate({}, stats_cfg_schema)


def test_valid_configuration(stats_cfg_schema, stats_cfg_martigny_data):
    """Test valid configuration."""
    validate(stats_cfg_martigny_data, stats_cfg_schema)


def test_valid_circulation_n_docs(stats_cfg_schema):
    """Test number of documents."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'catalog',
            'indicator': {
                'type': 'number_of_documents'
            }
        },
        'is_active': True
    }
    for dist in ['created_month', 'created_year', 'imported',
                 'owning_library']:
        data['category']['indicator']['distributions'] = [dist]
        validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_serial_holdings(stats_cfg_schema):
    """Test number of serial holdings."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'catalog',
            'indicator': {
                'type': 'number_of_serial_holdings'
            }
        },
        'is_active': True
    }
    for dist in ['created_month', 'created_year', 'owning_library']:
        data['category']['indicator']['distributions'] = [dist]
        validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_items(stats_cfg_schema):
    """Test number of items."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'catalog',
            'indicator': {
                'type': 'number_of_items'
            }
        },
        'is_active': True
    }
    for dist in ['created_month', 'created_year', 'owning_library',
                 'owning_location', 'document_type', 'document_subtype',
                 'type']:
        data['category']['indicator']['distributions'] = [dist]
        validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_patrons(stats_cfg_schema):
    """Test number of patrons."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'user_management',
            'indicator': {
                'type': 'number_of_patrons'
            }
        },
        'is_active': True
    }
    for dist in [
        'created_month', 'created_year', 'postal_code', 'type', 'gender',
        'birth_year', 'role'
    ]:
        data['category']['indicator']['distributions'] = [dist]
        validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_active_patrons(stats_cfg_schema):
    """Test number of active patrons."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'user_management',
            'indicator': {
                'type': 'number_of_active_patrons'
            }
        },
        'is_active': True
    }
    for period in ['year', 'month']:
        data['category']['indicator']['period'] = period
        for dist in [
            'created_month', 'created_year', 'postal_code', 'type', 'gender',
            'birth_year', 'role'
        ]:
            data['category']['indicator']['distributions'] = [dist]
            validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_deleted_items(stats_cfg_schema):
    """Test number of deleted items."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'catalog',
            'indicator': {
                'type': 'number_of_deleted_items'
            }
        },
        'is_active': True
    }
    for period in ['year', 'month']:
        data['category']['indicator']['period'] = period
        for dist in ['action_month', 'action_year', 'owning_library',
                     'operator_library']:
            data['category']['indicator']['distributions'] = [dist]
            validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)

    data['category']['indicator']['period'] = 'day'
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_ill_requests(stats_cfg_schema):
    """Test number of ill requests."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        "frequency": "month",
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'circulation',
            'indicator': {
                'type': 'number_of_ill_requests'
            }
        },
        'is_active': True
    }
    for dist in [
        'created_month', 'created_year', 'pickup_location', 'status'
    ]:
        data['category']['indicator']['distributions'] = [dist]
        validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_circulations(stats_cfg_schema):
    """Test number of ill requests."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'circulation',
            'indicator': {
            }
        },
        'is_active': True
    }
    for trigger in [
        'checkin'
    ]:
        data['category']['indicator']['type'] = f'number_of_{trigger}s'
        for period in ['year', 'month']:
            data['category']['indicator']['period'] = period
            for dist in [
                'transaction_month', 'transaction_year',
                'transaction_location', 'patron_type', 'patron_age',
                'patron_postal_code', 'document_type', 'transaction_channel',
                'owning_library', 'owning_location'
            ]:
                data['category']['indicator']['distributions'] = [dist]
                validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)

    data['category']['indicator']['period'] = 'day'
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_n_requests(stats_cfg_schema):
    """Test number of requests."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stat_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        "library": {
            "$ref": "https://bib.rero.ch/api/libraries/lib1"
        },
        'category': {
            'type': 'circulation',
            'indicator': {
            }
        },
        'is_active': True
    }
    for trigger in [
        'request'
    ]:
        data['category']['indicator']['type'] = f'number_of_{trigger}s'
        for period in ['year', 'month']:
            data['category']['indicator']['period'] = period
            for dist in [
                'transaction_month', 'transaction_year',
                'patron_type', 'patron_age',
                'patron_postal_code', 'document_type', 'transaction_channel',
                'owning_library', 'pickup_location', 'owning_location'
            ]:
                data['category']['indicator']['distributions'] = [dist]
                validate(data, stats_cfg_schema)

    data['category']['indicator']['distributions'] = ["foo"]
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)

    data['category']['indicator']['period'] = 'day'
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)
