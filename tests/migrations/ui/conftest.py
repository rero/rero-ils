# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest fixtures and plugins."""

import pytest


@pytest.fixture(scope="module")
def create_app():
    """Create test app."""
    # create_ui
    from invenio_app.factory import create_ui

    return create_ui
