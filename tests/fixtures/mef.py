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

"""Common pytest fixtures and plugins for MEF entities."""
from copy import deepcopy

import pytest

from rero_ils.modules.entities.remote_entities.api import \
    RemoteEntitiesSearch, RemoteEntity


@pytest.fixture(scope="module")
def mef_concept1_data(mef_entities):
    """Load MEF concept_1 data."""
    return deepcopy(mef_entities.get('concept_1'))


@pytest.fixture(scope="module")
def mef_concept1(mef_concept1_data):
    """Load MEF concept_1 data."""
    entity = RemoteEntity.create(
        data=mef_concept1_data,
        dbcommit=True,
        reindex=True,
        delete_pid=False
    )
    RemoteEntitiesSearch.flush_and_refresh()
    return entity


@pytest.fixture(scope="module")
def mef_concept1_data_tmp(mef_entities):
    """Load MEF concept_1 data."""
    return deepcopy(mef_entities.get('concept_1'))


@pytest.fixture(scope="module")
def mef_concept1_es_response(mef_concept1_data_tmp):
    """Get MEF ES response for `concept_1` entities."""
    # transform data to a valid MEF ES hit response
    data = deepcopy(mef_concept1_data_tmp)
    data['$schema'] = \
        'https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json'
    data.pop('type', None)

    return {'hits': {'hits': [{
        'id': data['idref']['pid'],
        'metadata': data
    }]}}


@pytest.fixture(scope="module")
def mef_concept2_es_response(mef_entities):
    """Load MEF es_concept_1 data."""
    return deepcopy(mef_entities.get('es_concepts_1'))


@pytest.fixture(scope="module")
def mef_agents1_es_response(mef_entities):
    """Load MEF es_agents_1 data."""
    return deepcopy(mef_entities.get('es_agents_1'))


@pytest.fixture(scope="module")
def mef_places1_es_response(mef_entities):
    """Load MEF es_places_1 data."""
    return deepcopy(mef_entities.get('es_places_1'))
