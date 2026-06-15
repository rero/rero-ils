# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Entities record tests."""

import pytest

from rero_ils.modules.commons.exceptions import RecordNotFound
from rero_ils.modules.entities.api import Entity
from rero_ils.modules.entities.helpers import get_entity_record_from_data
from rero_ils.modules.utils import get_ref_for_pid


def test_entities_properties(entity_person_data_tmp):
    """Test entity properties."""

    # These tests are only for code coverage
    entity = Entity(entity_person_data_tmp)
    with pytest.raises(NotImplementedError):
        entity.get_authorized_access_point(None)
    with pytest.raises(NotImplementedError):
        entity.resource_type


def test_entities_helpers(local_entity_org):
    """Test entity helpers"""
    data = {"pid": "dummy"}
    with pytest.raises(RecordNotFound):
        get_entity_record_from_data(data)

    data = {"$ref": get_ref_for_pid("locent", local_entity_org.pid)}
    assert get_entity_record_from_data(data) == local_entity_org
