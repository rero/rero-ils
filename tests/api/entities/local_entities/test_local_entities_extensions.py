# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests `LocalEntity` authorized access point."""


def test_local_entities_authorized_access_point(
    local_entity_person, local_entity_person2, local_entity_org, local_entity_org2
):
    """Test authorized access point calculation."""
    dumped_record = local_entity_person.dumps()
    assert dumped_record["authorized_access_point"] == "Loy, Georg (1881-1968)"
    dumped_record = local_entity_person2.dumps()
    assert dumped_record["authorized_access_point"] == "William III, King of England (1650-1702)"

    dumped_record = local_entity_org.dumps()
    assert dumped_record["authorized_access_point"] == "Convegno internazionale di Italianistica"
    #
    dumped_record = local_entity_org2.dumps()
    assert (
        dumped_record["authorized_access_point"] == "Catholic Church. Concilium Plenarium Americae "
        "Latinae (5th ; 1899 ; Rome, Italy)"
    )
