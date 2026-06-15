# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Template Record tests."""

import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.templates.api import Template
from rero_ils.modules.templates.api import template_id_fetcher as fetcher
from rero_ils.modules.utils import get_ref_for_pid


def test_template_create(db, search, templ_doc_public_martigny_data, org_martigny, system_librarian_martigny):
    """Test template creation."""
    templ_doc_public_martigny_data["toto"] = "toto"
    with pytest.raises(ValidationError):
        Template.create(templ_doc_public_martigny_data, delete_pid=True)
    db.session.rollback()

    next_pid = Template.provider.identifier.next()
    del templ_doc_public_martigny_data["toto"]
    temp = Template.create(templ_doc_public_martigny_data, delete_pid=True)
    next_pid += 1
    assert temp == templ_doc_public_martigny_data
    assert temp.get("pid") == str(next_pid)

    temp = Template.get_record_by_pid(str(next_pid))
    assert temp == templ_doc_public_martigny_data

    fetched_pid = fetcher(temp.id, temp)
    assert fetched_pid.pid_value == str(next_pid)
    assert fetched_pid.pid_type == "tmpl"


def test_template_can_delete(templ_doc_public_martigny):
    """Test can delete."""
    can, reasons = templ_doc_public_martigny.can_delete
    assert can
    assert reasons == {}


def test_template_replace_refs(templ_doc_public_martigny):
    """Test template replace_refs method."""
    tmpl = templ_doc_public_martigny
    tmpl.setdefault("data", {})["document"] = {"$ref": get_ref_for_pid("doc", "dummy_pid")}
    tmpl = tmpl.update(tmpl, dbcommit=True, reindex=True)
    assert "$ref" in tmpl["data"]["document"]
    assert "$ref" in tmpl["creator"]
    replace_data = tmpl.replace_refs()
    assert "$ref" in replace_data["data"]["document"]
    assert "$ref" not in replace_data["creator"]

    # reset changes
    del tmpl["data"]["document"]
    tmpl.update(tmpl, dbcommit=True, reindex=True)
