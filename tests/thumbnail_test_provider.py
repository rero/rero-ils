# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""In-memory thumbnail provider for the test suite.

``TestThumbnailProvider`` must be registered via the ``test_provider`` pytest
fixture (defined in ``tests/conftest.py``), which also sets
``RERO_INVENIO_THUMBNAILS_PROVIDERS = ["test"]`` in the app config.
Tests populate ``TestThumbnailProvider.covers`` to control which ISBNs get
a URL.

Example::

    # In a test or fixture:
    TestThumbnailProvider.covers["9781234567890"] = "https://test.example.com/cover.jpg"

    # All other ISBNs return (None, "test") — no cover added.
"""

from rero_invenio_thumbnails.contrib.api import BaseProvider


class TestThumbnailProvider(BaseProvider):
    """Deterministic in-memory thumbnail provider for the test suite.

    Uses a class-level ``covers`` dict so that all instances created by
    ``get_thumbnail_url`` share the same mapping without requiring injection
    into individual instances.
    """

    name = "test"
    covers = {}

    def get_thumbnail_url(self, isbn):
        """Return the pre-configured URL for *isbn*, or ``(None, "test")``."""
        return self.covers.get(isbn), "test"
