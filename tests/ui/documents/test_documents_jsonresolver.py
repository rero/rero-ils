# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document JSONResolver tests."""

import pytest
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from jsonref import JsonRefError


def test_documents_jsonresolver(db):
    """Test document json resolver."""
    rec = Record.create({"document": {"$ref": "https://bib.rero.ch/api/documents/doc1"}})
    pid = PersistentIdentifier.create("doc", "doc1", status=PIDStatus.NEW)
    # with pytest.raises(JsonRefError):
    assert rec.replace_refs().get("document") == {"type": "doc", "pid": "doc1"}

    pid.reserve()
    assert rec.replace_refs().get("document") == {"type": "doc", "pid": "doc1"}

    pid.register()
    assert rec.replace_refs().get("document") == {"type": "doc", "pid": "doc1"}

    pid2 = PersistentIdentifier.create("doc", "doc2", status=PIDStatus.REGISTERED)
    pid.redirect(pid2)
    assert rec.replace_refs().get("document") == {"type": "doc", "pid": "doc2"}

    pid.delete()
    assert rec.replace_refs().get("document") == {"type": "doc", "pid": "doc1"}

    # non existing record
    rec2 = Record.create({"document": {"$ref": "https://bib.rero.ch/api/documents/n_e"}})
    with pytest.raises(JsonRefError):
        # assert is required due to lazy loaded json reference
        assert rec2.replace_refs().get("document")
