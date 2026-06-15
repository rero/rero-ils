# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document record extension to add cover URL to electronicLocator."""

from flask import current_app
from invenio_records.extensions import RecordExtension
from rero_invenio_thumbnails import get_thumbnail_url

from rero_ils.modules.documents.tasks import enqueue_cover_url_update


class AddCoverUrlExtension(RecordExtension):
    """Record extension that appends a cover image locator derived from ISBN.

    Enqueues the document PID into a Redis-backed queue on both ``post_create``
    and ``post_commit``. The queue worker serializes all thumbnail lookups and
    runs them one at a time with a configurable delay, avoiding race conditions
    and external-service overload.

    Note: bulk-load paths (``fixture create`` without ``--dbcommit``, CSV
    import) do not fire extension hooks and are covered by the explicit
    ``add-cover-urls`` CLI command run at the end of setup.
    """

    def __init__(self, cached=True):
        """Initialize the extension.

        :param cached: Whether to use cached thumbnail lookups.
        """
        self.cached = cached

    @staticmethod
    def _has_cover(record):
        """Return True if the record already has a coverImage electronicLocator."""
        return any(loc.get("content") == "coverImage" for loc in record.get("electronicLocator", []))

    def find_cover_url(self, record):
        """Find the first available cover URL for a document's ISBNs.

        :param record: The document record to inspect.
        :returns: tuple (url, provider) or (None, None) if no cover was found.
        """
        isbns = [
            identified_by.get("value")
            for identified_by in record.get("identifiedBy", [])
            if identified_by.get("type") == "bf:Isbn" and identified_by.get("value")
        ]
        for isbn in sorted(set(isbns)):
            try:
                url, provider = get_thumbnail_url(isbn, cached=self.cached)
            except Exception as exc:
                current_app.logger.warning(f"Thumbnail lookup failed for ISBN {isbn}: {exc}", exc_info=True)
                continue
            if url:
                return url, provider
        return None, None

    def add_cover_url(self, record):
        """Append a coverImage electronicLocator to the record if one is missing.

        Does nothing if a coverImage locator already exists or if no thumbnail
        is found.

        :param record: The document record to mutate.
        :returns: ``True`` if a cover locator was added, ``False`` otherwise.
        """
        if self._has_cover(record):
            return False

        url, provider = self.find_cover_url(record)
        if not url:
            return False

        locator = {"type": "relatedResource", "content": "coverImage", "url": url}
        if provider:
            locator["publicNote"] = [f"rero-invenio-thumbnails provider: {provider}"]
        locators = record.get("electronicLocator", [])
        locators.append(locator)
        record["electronicLocator"] = locators
        return True

    @staticmethod
    def _has_isbn(record):
        """Return True if the record has at least one ISBN identifier."""
        return any(i.get("type") == "bf:Isbn" for i in record.get("identifiedBy", []))

    def _enqueue(self, record):
        """Enqueue the record PID for a cover URL lookup if no cover exists."""
        if self._has_isbn(record) and not self._has_cover(record):
            enqueue_cover_url_update(record["pid"], cached=self.cached)

    def post_create(self, record):
        """Enqueue an async cover URL lookup after the record is created.

        :param record: The document record that was just created.
        """
        self._enqueue(record)

    def post_commit(self, record):
        """Enqueue an async cover URL lookup after the record is committed.

        :param record: The document record that was just committed.
        """
        self._enqueue(record)
