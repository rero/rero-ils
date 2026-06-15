# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries search index mapping tests."""

from rero_ils.modules.templates.api import Template, TemplatesSearch
from tests.utils import get_mapping


def test_template_mapping(
    search,
    db,
    templ_doc_public_martigny_data,
    org_martigny,
    system_librarian_martigny,
    librarian_martigny,
):
    """Test template search index mapping."""
    search = TemplatesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    tmpl = Template.create(templ_doc_public_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    new_mapping = get_mapping(search.Meta.index)
    assert mapping == new_mapping
    tmpl.delete(force=True, dbcommit=True, delindex=True)


def test_template_search_mapping(app, templ_doc_public_martigny, templ_doc_private_martigny):
    """Test template search mapping."""
    search = TemplatesSearch()

    c = search.query("match", template_type="documents").count()
    assert c == 2
    c = search.query("match", organisation__pid="org1").count()
    assert c == 2
