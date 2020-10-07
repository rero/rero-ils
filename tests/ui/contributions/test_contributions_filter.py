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

"""Jinja2 filters tests."""

from rero_ils.modules.contributions.views import contribution_label, \
    contribution_merge_data_values


def test_contribution_label(app, contribution_person_data):
    """Test contributions merge data."""
    app.config['RERO_ILS_CONTRIBUTIONS_LABEL_ORDER'] = {
        'fallback': 'fr',
        'fr': ['rero', 'idref', 'gnd'],
        'de': ['gnd', 'rero', 'idref'],
    }
    label = contribution_label(contribution_person_data, 'fr')
    assert label == 'Loy, Georg, 1885-19..'
    label = contribution_label(contribution_person_data, 'it')
    assert label == 'Loy, Georg, 1885-19..'


def test_contribution_merge_data_values(app, contribution_person_data):
    """Test contributions merge data."""
    app.config['RERO_ILS_CONTRIBUTIONS_SOURCES'] = ['idref', 'gnd', 'rero']
    data = contribution_merge_data_values(contribution_person_data)
    assert data == {
        '$schema': {
            'https://mef.test.rero.ch/schemas/gnd/'
            'gnd-contribution-v0.0.1.json': ['gnd'],
            'https://mef.test.rero.ch/schemas/idref/'
            'idref-contribution-v0.0.1.json': ['idref']
        },
        'authorized_access_point': {
            'Loy, Georg, 1885': ['gnd'],
            'Loy, Georg, 1885-19..': ['idref']
        },
        'bf:Agent': {
            'bf:Person': ['idref', 'gnd']
        },
        'biographical_information': {
            'Diss. philosophische Fakultät': ['gnd']
        },
        'country_associated': {
            'gw': ['idref']
        },
        'date_of_birth': {
            '1885': ['gnd'],
            '1885-05-14': ['idref']
        },
        'date_of_death': {
            '19..': ['idref']
        },
        'identifier': {
            'http://d-nb.info/gnd/13343771X': ['gnd'],
            'http://www.idref.fr/223977268': ['idref']
        },
        'language': {
            'ger': ['idref']
        },
        'md5': {
            '3dd3788c64af4200676a35a5ea35b180': ['idref'],
            '5dad1e77d5a47d39e87bb0ec37aaf51e': ['gnd']
        },
        'pid': {
            '13343771X': ['gnd'],
            '223977268': ['idref']
        },
        'preferred_name': {
            'Loy, Georg': ['idref', 'gnd']
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
        }
    }
