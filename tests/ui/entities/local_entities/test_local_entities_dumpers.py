# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Items Record dumper tests."""

from rero_ils.modules.entities.dumpers import document_dumper


def test_local_entities_document_dumper(local_entity_person2):
    """Test document dumper."""

    dumped_record = local_entity_person2.dumps(dumper=document_dumper)
    authorized_access_point = "William III, King of England (1650-1702)"
    for field in [
        "authorized_access_point_de",
        "authorized_access_point_en",
        "authorized_access_point_fr",
        "authorized_access_point_it",
    ]:
        assert dumped_record[field] == authorized_access_point
