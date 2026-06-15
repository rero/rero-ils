# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Selfcheck admin."""

import pytest
from invenio_db import db
from sqlalchemy.exc import IntegrityError

from rero_ils.modules.selfcheck.models import SelfcheckTerminal


def test_selfcheckuser(app):
    """Test SelfcheckUser model."""

    selfcheck_terminal = SelfcheckTerminal(
        name="selfcheck_test",
        access_token="UNACCESSTOKENDETEST",
        organisation_pid="org1",
        library_pid="lib1",
        location_pid="loc1",
        comments="a new comment",
    )
    # 1. test create selfcheck user
    assert not selfcheck_terminal.active
    db.session.add(selfcheck_terminal)
    db.session.commit()
    selfcheck_terminal_id = selfcheck_terminal.id
    assert selfcheck_terminal.active
    selfcheck_terminals = SelfcheckTerminal.query.all()
    assert len(selfcheck_terminals) == 1

    # 2. test update selfcheck user
    selfcheck_terminal_patch = SelfcheckTerminal(
        id=selfcheck_terminal_id,
        name="selfcheck_test_modified",
        access_token="UNACCESSTOKENDETEST",
        organisation_pid="org1",
        library_pid="lib1",
        location_pid="loc1",
        comments="an updated comment",
    )
    db.session.merge(selfcheck_terminal_patch)
    db.session.commit()

    # 3. test unique name for selfcheck terminal
    selfcheck_terminal = SelfcheckTerminal(
        name="selfcheck_test_modified",
        access_token="UNACCESSTOKENDETEST",
        organisation_pid="org1",
        library_pid="lib1",
        location_pid="loc2",
        comments="a third comment",
    )
    db.session.add(selfcheck_terminal)
    with pytest.raises(IntegrityError):
        db.session.commit()
