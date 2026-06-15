# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest libraries."""

import pytest


@pytest.fixture(scope="module")
def libraries_records(lib_martigny, lib_saxon, lib_fully, lib_sion, lib_aproz):
    """Libraries for test mapping."""
