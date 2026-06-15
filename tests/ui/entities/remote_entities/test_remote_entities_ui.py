# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Jinja2 filters tests."""

from rero_ils.modules.entities.views import entity_label


def test_remote_entity_label(app, entity_person_data):
    """Test entity label."""
    app.config["RERO_ILS_AGENTS_LABEL_ORDER"] = {
        "fallback": "fr",
        "fr": ["rero", "idref", "gnd"],
        "de": ["gnd", "rero", "idref"],
    }
    label = entity_label(entity_person_data, "fr")
    assert label == "Loy, Georg, 1885-19.."
    label = entity_label(entity_person_data, "it")
    assert label == "Loy, Georg, 1885-19.."
