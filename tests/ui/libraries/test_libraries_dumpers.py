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

"""Library Record dumpers."""
import pytest

from rero_ils.modules.commons.exceptions import MissingDataException
from rero_ils.modules.libraries.dumpers import \
    LibraryAcquisitionNotificationDumper, \
    LibrarySerialClaimNotificationDumper


def test_library_serial_dumpers(lib_martigny, lib_saxon):
    """Test serial library dumpers."""

    # Acquisition dumper
    dump_data = lib_martigny.dumps(LibraryAcquisitionNotificationDumper())
    assert dump_data['shipping_informations']
    assert dump_data['billing_informations']
    dump_data = lib_saxon.dumps(LibraryAcquisitionNotificationDumper())
    assert dump_data['shipping_informations']
    assert 'billing_informations' not in dump_data

    # Claim issue dumper
    data = lib_martigny.dumps(LibrarySerialClaimNotificationDumper())
    assert data['address']
    assert data['shipping_informations']
    assert data['billing_informations']
    with pytest.raises(MissingDataException) as exc:
        lib_saxon.dumps(LibrarySerialClaimNotificationDumper())
    assert 'library.serial_acquisition_settings' in str(exc)
