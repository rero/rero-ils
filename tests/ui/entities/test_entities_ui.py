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

"""Tests UI view for entities."""

from flask import url_for


def test_entity_person_detailed_view(client, entity_person):
    """Test entity person detailed view."""
    res = client.get(url_for(
        'entities.persons_proxy',
        viewcode='global', pid=entity_person.pid))
    assert res.status_code == 200


def test_entity_organisation_detailed_view(client, entity_organisation):
    """Test entity organisation detailed view."""
    res = client.get(url_for(
        'entities.corporate_bodies_proxy',
        viewcode='global', pid='ent_org'))
    assert res.status_code == 200
