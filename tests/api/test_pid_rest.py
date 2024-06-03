# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""API tests for PID and IlsRecords"""

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.locations.api import Location


def test_ilsrecord_pid_after_validationerror(
    client, loc_online_martigny_data, librarian_martigny
):
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
