# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest libraries."""

import pytest


@pytest.fixture(scope="module")
def local_fields_records(local_field_martigny, local_field_sion):
    """Local fields for test mapping."""
