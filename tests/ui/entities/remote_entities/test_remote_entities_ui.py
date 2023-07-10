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

from rero_ils.modules.entities.views import entity_label


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
