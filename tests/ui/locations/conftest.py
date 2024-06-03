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

"""Common pytest libraries."""

import pytest


@pytest.fixture(scope="module")
def locations_records(
    loc_public_martigny,
    loc_restricted_martigny,
    loc_public_saxon,
    loc_restricted_saxon,
    loc_public_fully,
    loc_restricted_fully,
    loc_public_sion,
    loc_restricted_sion,
    loc_online_martigny,
    loc_online_saxon,
    loc_online_fully,
    loc_online_sion,
    loc_online_aproz,
):
    """Locations for test mapping."""
