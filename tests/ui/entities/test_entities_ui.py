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
from invenio_i18n.ext import current_i18n

from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.entities.views import entity_icon, \
    extract_data_from_remote_entity, search_link, sources_link


def test_view(client, entity_person, local_entity_person):
    """Entity detailed view test."""

    # Check unauthorized type value in url
    res = client.get(url_for(
        'entities.entity_detailed_view',
        viewcode='global',
        type='foo',
        pid='foo'
    ))
    assert res.status_code == 404

    # Check 404 error if entity does not exist
    res = client.get(url_for(
        'entities.entity_detailed_view',
        viewcode='global',
        type='remote',
        pid='foo'
    ))
    assert res.status_code == 404

    # Remote entity
    res = client.get(url_for(
        'entities.entity_detailed_view',
        viewcode='global',
        type='remote',
        pid=entity_person.get('pid')
    ))
    assert res.status_code == 200

    # Local entity
    res = client.get(url_for(
        'entities.entity_detailed_view',
        viewcode='global',
        type='local',
        pid=local_entity_person.get('pid')
    ))
    assert res.status_code == 200


def test_entity_icon():
    """Entity icon test."""
    assert 'fa-building-o' == entity_icon(EntityType.ORGANISATION)
    # Default icon if type not found
    assert 'fa-question-circle-o' == entity_icon('foo')


def test_extract_data_from_record(app):
    """Extract data from record test."""
    contrib_data = {
        'idref': {'data': 'idref'},
        'rero': {'data': 'rero'},
        'gnd': {'data': 'gnd'}
    }
    current_i18n.locale.language = 'fr'
    source, data = extract_data_from_remote_entity(contrib_data)
    assert source == 'idref'
    assert contrib_data.get(source) == data

    current_i18n.locale.language = 'de'
    source, data = extract_data_from_remote_entity(contrib_data)
    assert source == 'gnd'
    assert contrib_data.get(source) == data

    # Fallback test
    current_i18n.locale.language = 'it'
    source, data = extract_data_from_remote_entity(contrib_data)
    assert source == 'idref'
    assert contrib_data.get(source) == data

    # Control the selection cascade
    contrib_data.pop('idref')
    contrib_data.pop('gnd')
    source, data = extract_data_from_remote_entity(contrib_data)
    assert source == 'rero'
    assert contrib_data.get(source) == data


def test_sources_link(app):
    """Sources link test."""
    data = {
        'idref': {'identifier': 'http://www.idref.fr/066924502'},
        'gnd': {'identifier': 'http://d-nb.info/gnd/118754688'},
        'rero': {'identifier': 'http://data.rero.ch/02-A003795108'},
        'sources': ['idref', 'gnd', 'rero']
    }
    result = {
        'idref': 'http://www.idref.fr/066924502',
        'gnd': 'http://d-nb.info/gnd/118754688'
    }
    assert result == sources_link(data)
    assert {} == sources_link({})


def test_search_link(app, entity_organisation, local_entity_org, entity_topic):
    """Search link test."""

    # test remote link
    link = search_link(entity_organisation)
    assert link == 'contribution.entity.pids.rero:A027711299 ' \
        'OR subjects.entity.pids.rero:A027711299' \
        '&simple=0'
    # test local link
    link = search_link(local_entity_org)
    assert link == 'contribution.entity.pids.local:locent_org ' \
        'OR subjects.entity.pids.local:locent_org' \
        '&simple=0'
    # test Topic
    link = search_link(entity_topic)
    assert link == 'subjects.entity.pids.idref:030752787 ' \
        'OR genreForm.entity.pids.idref:030752787' \
        '&simple=0'
