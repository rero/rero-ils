# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Patrons record dumper tests."""
from rero_ils.modules.patrons.dumpers import PatronPropertiesDumper


def test_patron_properties_dumper(patron_martigny):
    """Test patron properties dumper."""
    dumper = PatronPropertiesDumper(["formatted_name", "dummy"])
    dumped_data = patron_martigny.dumps(dumper=dumper)
    assert "formatted_name" in dumped_data
    assert "dummy" not in dumped_data
