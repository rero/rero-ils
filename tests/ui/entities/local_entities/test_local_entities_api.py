# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entities record tests."""

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.utils import get_ref_for_pid


def test_local_entity_properties(local_entity_person):
    """Test local entity property"""
    assert local_entity_person.get_authorized_access_point(None) == local_entity_person["authorized_access_point"]


def test_local_entity_indexing(app, local_entity_person, document_data_tmp):
    """Test local entity indexing."""
    entity = local_entity_person

    # Check relations between local entity and other resources.
    data = document_data_tmp
    data.setdefault("contribution", []).append(
        {"entity": {"$ref": get_ref_for_pid("locent", entity.pid)}, "role": ["aut"]}
    )
    doc = Document.create(data, delete_pid=True, reindex=True, dbcommit=True)
    reasons = entity.reasons_not_to_delete()
    assert reasons["links"]["documents"]

    # Update the local entity and check if related resources are updated
    original_access_point = entity["authorized_access_point"]
    entity["name"] = "my_local_access_point"
    entity = entity.update(entity, dbcommit=True, reindex=True, commit=True)
    # index_referenced_records runs synchronously via CELERY_TASK_ALWAYS_EAGER
    DocumentsSearch.flush_and_refresh()
    hit = DocumentsSearch().get_record_by_pid(doc.pid)
    assert any(
        contribution["entity"]["authorized_access_point_fr"] == entity.get_authorized_access_point(language="fr")
        for contribution in hit.contribution
    )

    # reset fixtures
    entity["authorized_access_point"] = original_access_point
    entity.update(entity, dbcommit=True, reindex=True)
    doc.delete()
