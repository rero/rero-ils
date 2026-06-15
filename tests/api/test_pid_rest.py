# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API tests for PID and IlsRecords"""

from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.locations.api import Location
from tests.utils import postdata


def test_ilsrecord_pid_after_validationerror(client, loc_online_martigny_data, librarian_martigny):
    """Check PID before and after a ValidationError: it should be the same"""
    loc = Location.create(loc_online_martigny_data, delete_pid=True)
    next_pid = str(int(loc.pid) + 1)

    # post invalid data and post them
    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(
        client,
        "invenio_records_rest.loc_list",
        {
            "$schema": "https://bib.rero.ch/schemas/locations/location-v0.0.1.json",
            "library": {"$ref": "https://bib.rero.ch/api/libraries/lib1"},
            "name": "Library of Foo",
        },
    )

    # check http status for invalid record
    assert res.status_code == 400

    # the pid should be unchanged
    loc.provider.identifier.query.first().recid == loc.pid

    # check that we can create a new location
    loc2 = Location.create(loc_online_martigny_data, delete_pid=True)
    loc2.pid == next_pid
