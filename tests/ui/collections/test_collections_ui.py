# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Tests UI view for collections."""

from flask import url_for


def test_collection_detailed_view_without_library(client, coll_saxon_1):
    """Test collection detailed view."""
    # check redirection
    res = client.get(
        url_for("invenio_records_ui.coll", viewcode="org1", pid_value=coll_saxon_1.pid)
    )
    assert res.status_code == 200


def test_collection_detailed_view(client, coll_martigny_1):
    """Test collection detailed view."""
    # check redirection
    res = client.get(
        url_for(
            "invenio_records_ui.coll", viewcode="org1", pid_value=coll_martigny_1.pid
        )
    )
    assert res.status_code == 200
