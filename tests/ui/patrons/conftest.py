# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest patrons."""

import pytest


@pytest.fixture(scope="module")
def patrons_records(patron_martigny, patron2_martigny, librarian_sion, librarian_saxon):
    """Patrons for test mapping."""
