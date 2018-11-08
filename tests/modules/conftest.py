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

"""Pytest configuration."""

import pytest

# TODO: get url dynamiclly
url_schema = 'http://ils.test.rero.ch/schema'


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Create test app."""
    from invenio_app.factory import create_app as create_ui_api
    return create_ui_api


@pytest.yield_fixture()
def minimal_circ_policy_record():
    """Simple patron record."""
    yield {
        '$schema': url_schema + '/circ_policies/circ_policy-v0.0.1.json',
        'pid': '1',
        'name': 'standard',
        'description': 'default standard circulation policy',
        'organisation_pid': '1',
        'allow_checkout': True,
        'checkout_duration': 30,
        'allow_requests': True,
        'number_renewals': 3,
        'renewal_duration': 30
    }


@pytest.yield_fixture()
def minimal_patron_only_record():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '2',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'barcode': '2050124311',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type_pid': '1',
        'is_staff': False,
        'is_patron': True
    }


@pytest.yield_fixture()
def minimal_staff_only_record():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '3',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'library_pid': '1',
        'is_staff': True,
        'is_patron': False
    }


@pytest.yield_fixture()
def minimal_staff_patron_record():
    """Simple patron record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema/patrons/patron-v0.0.1.json',
        'pid': '3',
        'first_name': 'Simonetta',
        'last_name': 'Casalini',
        'street': 'Avenue Leopold-Robert, 132',
        'barcode': '2050124311',
        'postal_code': '2300',
        'city': 'La Chaux-de-Fonds',
        'birth_date': '1967-06-07',
        'email': 'simolibri07@gmail.com',
        'phone': '+41324993585',
        'patron_type_pid': '1',
        'is_staff': True,
        'is_patron': True
    }


@pytest.yield_fixture()
def minimal_organisation_record():
    """Simple organisation record."""
    yield {
        '$schema': url_schema + '/organisations/organisation-v0.0.1.json',
        'pid': '1',
        'name': 'MV Sion',
        'address': 'address'
    }


@pytest.yield_fixture()
def person_data():
    """Person data."""
    yield {
        "bnf": {
            "date_of_birth": "1525",
            "identifier_for_person": "10008312",
            "variant_name_for_person": [
                "Cavaleriis, Joannes-Baptista de",
                "Cavalieri, Giovanni-Battista de'",
            ]
        },
        "gnd": {
            "date_of_birth": "ca. 1525",
            "identifier_for_person": "12391664X",
            "preferred_name_for_person": "Cavalieri, Giovanni Battista",
            "variant_name_for_person": [
                "Cavaleriis, Joannes-Baptista de",
                "Cavaleriis, Joannes Baptista",
            ]
        },
        "pid": "1",
        "rero": {
            "date_of_birth": "ca.1525-1601",
            "identifier_for_person": "A023655346",
            "variant_name_for_person": [
                "Cavaleriis, Joannes-Baptista de",
                "Cavaleriis, Joannes Baptista",
            ]
        },
        "viaf_pid": "66739143"
    }


@pytest.yield_fixture()
def person_data_result():
    """Person data result."""
    yield {
        'date_of_birth': {
            '1525': ['bnf'], 'ca. 1525': ['gnd'], 'ca.1525-1601': ['rero']
        },
        'identifier_for_person': {
            '10008312': ['bnf'], '12391664X': ['gnd'], 'A023655346': ['rero']
        },
        'variant_name_for_person': {
            'Cavaleriis, Joannes-Baptista de': ['bnf', 'gnd', 'rero'],
            "Cavalieri, Giovanni-Battista de'": ['bnf'],
            'Cavaleriis, Joannes Baptista': ['gnd', 'rero']
        },
        'preferred_name_for_person': {
            'Cavalieri, Giovanni Battista': ['gnd']
        }
    }


@pytest.yield_fixture()
def document_data_authors():
    """Document with authors."""
    yield [
        {
            'name': 'Foo'
        },
        {
            'name': 'Bar',
            'qualifier': 'prof',
            'date': '2018'
        }
    ]


@pytest.yield_fixture()
def document_data_publishers():
    """Document with publishers."""
    yield [
        {
            'name': [
                'Foo'
            ]
        },
        {
            'place': [
                'place1',
                'place2'
            ],
            'name': [
                'Foo',
                'Bar'
            ]
        }
    ]


@pytest.yield_fixture()
def document_data_series():
    """Document with series."""
    yield [
        {
            'name': 'serie 1'
        },
        {
            'name': 'serie 2',
            'number': '2018'
        }
    ]


@pytest.yield_fixture()
def document_data_abstracts():
    """Document with abstracts."""
    yield [
        'line1\n\n\nline2',
        'line3'
    ]


@pytest.yield_fixture()
def form_locations_pids_names():
    """Form options with resolve: form_locations_pids_names."""
    form = [{
        'items': [{
            'key': 'location_pid',
            'populate': 'locations_pids_names',
        }]
    }]
    yield form


@pytest.yield_fixture()
def form_item_types_names_descriptions():
    """Form options with resolve: item_types_names_descriptions."""
    form = [{
        'items': [{
            'key': 'item_type_pid',
            'populate': 'item_types_names_descriptions',
        }]
    }]
    yield form


@pytest.yield_fixture()
def form_patron_names_descriptions():
    """Form options with resolve: patron_names_descriptions."""
    form = [{
        'items': [{
            'key': 'patron_type_pid',
            'populate': 'patron_names_descriptions',
        }]
    }]
    yield form
