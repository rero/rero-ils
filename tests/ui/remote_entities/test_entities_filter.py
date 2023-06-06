# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Jinja2 filters tests."""

from rero_ils.modules.remote_entities.views import entity_label, \
    entity_merge_data_values


def test_remote_entity_label(app, entity_person_data):
    """Test entity label."""
    app.config['RERO_ILS_AGENTS_LABEL_ORDER'] = {
        'fallback': 'fr',
        'fr': ['rero', 'idref', 'gnd'],
        'de': ['gnd', 'rero', 'idref'],
    }
    label = entity_label(entity_person_data, 'fr')
    assert label == 'Loy, Georg, 1885-19..'
    label = entity_label(entity_person_data, 'it')
    assert label == 'Loy, Georg, 1885-19..'


def test_remote_entity_merge_data_values(app, entity_person_data):
    """Test entities merge data."""
    app.config['RERO_ILS_AGENTS_SOURCES'] = ['idref', 'gnd', 'rero']
    data = entity_merge_data_values(entity_person_data)
    assert data == {
        '$schema': {
            'https://mef.test.rero.ch/schemas/gnd/'
            'gnd-contribution-v0.0.1.json': ['gnd'],
            'https://mef.test.rero.ch/schemas/idref/'
            'idref-contribution-v0.0.1.json': ['idref'],
            'https://mef.test.rero.ch/schemas/rero/'
            'rero-contribution-v0.0.1.json': ['rero']
        },
        'authorized_access_point': {
            'Loy, Georg, 1885': ['gnd'],
            'Loy, Georg, 1885-19..': ['idref', 'rero']
        },
        'bf:Agent': {
            'bf:Person': ['idref', 'gnd', 'rero']
        },
        'biographical_information': {
            'Diss. philosophische Fakultät': ['gnd']
        },
        'country_associated': {
            'gw': ['idref', 'rero']
        },
        'date_of_birth': {
            '1885': ['gnd'],
            '1885-05-14': ['idref', 'rero']
        },
        'date_of_death': {
            '19..': ['idref', 'rero']
        },
        'identifier': {
            'http://d-nb.info/gnd/13343771X': ['gnd'],
            'http://www.idref.fr/223977268': ['idref'],
            'http://data.rero.ch/02-A017671081': ['rero']
        },
        'language': {
            'ger': ['idref', 'rero']
        },
        'md5': {
            '3dd3788c64af4200676a35a5ea35b180': ['idref'],
            '3dd3788c64af4200676a35a5ea35b181': ['rero'],
            '5dad1e77d5a47d39e87bb0ec37aaf51e': ['gnd']
        },
        'pid': {
            '13343771X': ['gnd'],
            '223977268': ['idref'],
            'A017671081': ['rero']
        },
        'preferred_name': {
            'Loy, Georg': ['idref', 'gnd', 'rero']
        },
        'variant_name': {
            'Loy, George, di Madeiros': ['gnd']
        },
        'gnd': {
            'identifier': 'http://d-nb.info/gnd/13343771X',
            'pid': '13343771X'
        },
        'idref': {
            'identifier': 'http://www.idref.fr/223977268',
            'pid': '223977268'
        },
        'rero': {
            'identifier': 'http://data.rero.ch/02-A017671081',
            'pid': 'A017671081'
        }

    }
