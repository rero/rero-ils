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


def test_valid_catalogue_category(stats_cfg_schema):
    """Test valid catalogue category field."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stats_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        'organisation': {
            '$ref': 'https://bib.rero.ch/api/organisations/org1'
        },
        'category': {
            'type': 'catalogue',
            'indicator': {
                'type': 'number_of_documents',
                'distributions': [
                    'time_range_month'
                ],
                'filter': 'foo=bar'
            }
        },
        'is_active': True
    }
    validate(data, stats_cfg_schema)


def test_invalid_catalogue_category(stats_cfg_schema):
    """Test valid catalogue category field."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stats_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        'organisation': {
            '$ref': 'https://bib.rero.ch/api/organisations/org1'
        },
        'category': {
            'type': 'catalogue',
            'indicator': {
                'type': 'number_of_documents',
                'distributions': [
                    'item_location'
                ]
            }
        },
        'is_active': True
    }
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)


def test_valid_circulation_category(stats_cfg_schema):
    """Test valid circulation category field."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stats_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        'organisation': {
            '$ref': 'https://bib.rero.ch/api/organisations/org1'
        },
        'category': {
            'type': 'circulation',
            'indicator': {
                'type': 'number_of_checkins',
                'distributions': [
                    'time_range_month',
                    'library'
                ],
                'period': 'month',
                'filter': 'foo=bar'
            }
        },
        'is_active': True
    }
    validate(data, stats_cfg_schema)


def test_invalid_circulation_category_period(stats_cfg_schema):
    """Test invalid period field."""
    data = {
        '$schema':
            'https://bib.rero.ch/schemas/stats_cfg/stats_cfg-v0.0.1.json',
        'pid': 'statcfg1',
        'name': 'foo',
        'description': 'bar',
        'frequency': 'month',
        'organisation': {
            '$ref': 'https://bib.rero.ch/api/organisations/org1'
        },
        'category': {
            'type': 'circulation',
            'indicator': {
                'type': 'number_of_checkins',
                'distributions': [
                    'time_range_month',
                    'library'
                ],
                'period': 'day',
                'filter': 'foo=bar'
            }
        },
        'is_active': True
    }
    with pytest.raises(ValidationError):
        validate(data, stats_cfg_schema)
