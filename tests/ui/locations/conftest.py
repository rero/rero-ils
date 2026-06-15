# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
