# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest fixtures and plugins for MEF entities."""

from copy import deepcopy

import pytest

from rero_ils.modules.entities.remote_entities.api import (
    RemoteEntitiesSearch,
    RemoteEntity,
)


@pytest.fixture(scope="module")
def mef_concept1_data(mef_entities):
    """Load MEF concept_1 data."""
    return deepcopy(mef_entities.get("concept_1"))


@pytest.fixture(scope="module")
def mef_concept1(mef_concept1_data):
    """Load MEF concept_1 data."""
    entity = RemoteEntity.create(data=mef_concept1_data, dbcommit=True, reindex=True, delete_pid=False)
    RemoteEntitiesSearch.flush_and_refresh()
    return entity


@pytest.fixture(scope="module")
def mef_concept1_data_tmp(mef_entities):
    """Load MEF concept_1 data."""
    return deepcopy(mef_entities.get("concept_1"))


@pytest.fixture(scope="module")
def mef_concept1_search_response(mef_concept1_data_tmp):
    """Get MEF search response for `concept_1` entities."""
    # transform data to a valid MEF search hit response
    data = deepcopy(mef_concept1_data_tmp)
    data["$schema"] = "https://mef.rero.ch/schemas/concepts_mef/mef-concept-v0.0.1.json"
    data.pop("type", None)

    return {"hits": {"hits": [{"id": data["idref"]["pid"], "metadata": data}]}}


@pytest.fixture(scope="module")
def mef_concept2_search_response(mef_entities):
    """Load MEF search_concept_1 data."""
    return deepcopy(mef_entities.get("search_concepts_1"))


@pytest.fixture(scope="module")
def mef_agents1_search_response(mef_entities):
    """Load MEF search_agents_1 data."""
    return deepcopy(mef_entities.get("search_agents_1"))


@pytest.fixture(scope="module")
def mef_places1_search_response(mef_entities):
    """Load MEF search_places_1 data."""
    return deepcopy(mef_entities.get("search_places_1"))
