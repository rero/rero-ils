# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""In-memory thumbnail provider for the test suite.

Registered by the ``test_provider`` fixture; tests set ISBN cover URLs through the ``thumbnail_covers`` fixture.
"""

from rero_invenio_thumbnails.contrib.api import BaseProvider


class TestThumbnailProvider(BaseProvider):
    """Deterministic in-memory thumbnail provider for the test suite.

    ``covers`` is a class attribute, as the providers are instantiated by ``get_thumbnail_url``.
    """

    name = "test"
    covers = {}

    def get_thumbnail_url(self, isbn):
        """Return the pre-configured URL for *isbn*, or ``(None, "test")``."""
        return self.covers.get(isbn), "test"
