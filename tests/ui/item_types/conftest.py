# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest item_types."""

import pytest


@pytest.fixture(scope="module")
def item_types_records(
    item_type_standard_martigny,
    item_type_on_site_martigny,
    item_type_specific_martigny,
    item_type_regular_sion,
):
    """Item types for test mapping."""
