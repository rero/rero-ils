# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Ill request record tests."""

from unittest import mock

from rero_ils.modules.ill_requests.utils import get_pickup_location_options


def test_get_pickup_location_options(patron_martigny, loc_public_martigny, loc_restricted_martigny):
    """Test pickup location options from utils."""
    with mock.patch("rero_ils.modules.ill_requests.utils.current_patrons", [patron_martigny]):
        assert loc_public_martigny.get("is_pickup", False)
        assert not loc_restricted_martigny.get("is_pickup", False)

        options = list(get_pickup_location_options())
        assert len(options) == 1
        assert options[0][0] == loc_public_martigny.pid
