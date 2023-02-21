# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Test library dumpers."""

from rero_ils.modules.libraries.dumpers import \
    LibraryAcquisitionNotificationDumper


def test_library_dumpers(lib_martigny, lib_saxon):
    """Test library dumpers."""

    dump_data = lib_martigny.dumps(
        dumper=LibraryAcquisitionNotificationDumper())
    assert dump_data['shipping_informations']
    assert dump_data['billing_informations']

    dump_data = lib_saxon.dumps(
        dumper=LibraryAcquisitionNotificationDumper())
    assert dump_data['shipping_informations']
    assert 'billing_informations' not in dump_data
