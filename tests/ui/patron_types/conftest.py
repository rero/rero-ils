# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest patron_types."""

import pytest


@pytest.fixture(scope="module")
def patron_types_records(patron_type_adults_martigny, patron_type_youngsters_sion, patron_type_grown_sion):
    """Patron types for test mapping."""
