# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest fixtures and plugins for the UI application."""

import pytest


@pytest.fixture(scope="module")
def create_app():
    """Create test app."""
    from invenio_app.factory import create_app as create_ui_api

    return create_ui_api
