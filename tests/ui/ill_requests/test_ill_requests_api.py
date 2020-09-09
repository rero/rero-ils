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

from __future__ import absolute_import, print_function


def test_ill_request_properties(ill_request_martigny, ill_request_sion,
                                loc_public_martigny_data, org_martigny_data):
    """Test ill request properties."""
    assert not ill_request_martigny.is_copy
    assert ill_request_sion.is_copy

    assert ill_request_martigny.get_pickup_location().pid \
        == loc_public_martigny_data['pid']
    assert ill_request_martigny.organisation_pid == org_martigny_data['pid']
