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

"""Ill request record tests."""

from rero_ils.modules.ill_requests.api import ILLRequest
from rero_ils.modules.ill_requests.models import ILLRequestNoteStatus


def test_ill_request_properties(
    ill_request_martigny,
    ill_request_sion,
    loc_public_martigny_data,
    org_martigny_data,
    lib_martigny,
):
    """Test ill request properties."""
    assert not ill_request_martigny.is_copy
    assert ill_request_sion.is_copy

    assert (
        ill_request_martigny.get_pickup_location().pid
        == loc_public_martigny_data["pid"]
    )
    assert ill_request_martigny.organisation_pid == org_martigny_data["pid"]

    # test notes
    assert ill_request_martigny.public_note is None
    note_content = "public note test"
    ill_request_martigny["notes"] = [
        {"type": ILLRequestNoteStatus.PUBLIC_NOTE, "content": note_content}
    ]
    assert ill_request_martigny.public_note == note_content
    ill_request_martigny["notes"] = [
        {"type": ILLRequestNoteStatus.STAFF_NOTE, "content": note_content}
    ]
    assert ill_request_martigny.public_note is None
    del ill_request_martigny["notes"]

    assert ill_request_martigny.get_library().pid == lib_martigny.pid


def test_ill_request_get_request(
    ill_request_martigny, ill_request_sion, patron_martigny
):
    """Test ill request get_request functions."""
    assert (
        len(
            list(
                ILLRequest.get_requests_by_patron_pid(
                    patron_martigny.pid, status="pending"
                )
            )
        )
        == 1
    )
    assert (
        len(
            list(
                ILLRequest.get_requests_by_patron_pid(
                    patron_martigny.pid, status="denied"
                )
            )
        )
        == 0
    )
