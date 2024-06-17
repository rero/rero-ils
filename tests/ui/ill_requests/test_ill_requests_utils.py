# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

from __future__ import absolute_import, print_function

import mock

from rero_ils.modules.ill_requests.utils import get_pickup_location_options


def test_get_pickup_location_options(
    patron_martigny, loc_public_martigny, loc_restricted_martigny
):
    """Test pickup location options from utils."""
    with mock.patch(
        "rero_ils.modules.ill_requests.utils.current_patrons", [patron_martigny]
    ):
        assert loc_public_martigny.get("is_pickup", False)
        assert not loc_restricted_martigny.get("is_pickup", False)

        options = list(get_pickup_location_options())
        assert len(options) == 1
        assert options[0][0] == loc_public_martigny.pid
