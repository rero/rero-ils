# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Library Record dumpers."""

import pytest

from rero_ils.modules.commons.exceptions import MissingDataException
from rero_ils.modules.libraries.dumpers import (
    LibraryAcquisitionNotificationDumper,
    LibrarySerialClaimNotificationDumper,
)


def test_library_serial_dumpers(lib_martigny, lib_saxon):
    """Test serial library dumpers."""

    # Acquisition dumper
    dump_data = lib_martigny.dumps(LibraryAcquisitionNotificationDumper())
    assert dump_data["shipping_informations"]
    assert dump_data["billing_informations"]
    dump_data = lib_saxon.dumps(LibraryAcquisitionNotificationDumper())
    assert dump_data["shipping_informations"]
    assert "billing_informations" not in dump_data

    # Claim issue dumper
    data = lib_martigny.dumps(LibrarySerialClaimNotificationDumper())
    assert data["address"]
    assert data["shipping_informations"]
    assert data["billing_informations"]
    with pytest.raises(MissingDataException) as exc:
        lib_saxon.dumps(LibrarySerialClaimNotificationDumper())
    assert "library.serial_acquisition_settings" in str(exc)
