# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2026 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Document record extension to add cover URL to electronicLocator."""

from flask import current_app
from invenio_records.extensions import RecordExtension
from rero_invenio_thumbnails import get_thumbnail_url


class AddCoverUrlExtension(RecordExtension):
    """Record extension that appends a cover image locator derived from ISBN."""

    def __init__(self, cached=True):
        """Initialize the extension.

        :param cached: Whether to use cached thumbnail lookups.
        """
        self.cached = cached

    def add_cover_url(self, record):
        """Append a coverImage electronicLocator to the record if one is missing.

        Iterates over the record's ISBNs in sorted order and calls
        ``get_thumbnail_url`` for each until a URL is found. Skips ISBNs
        that raise an exception. Does nothing if a coverImage locator already
        exists or if the record has no ISBNs.

        :param record: The document record to mutate.
        :returns: ``True`` if a cover locator was added, ``False`` otherwise.
        """

        # Check if cover image already exists
        electronic_locators = record.get("electronicLocator", [])
        has_cover = any(loc.get("content") == "coverImage" for loc in electronic_locators)

        if has_cover:
            return False

        # Get ISBNs from identifiedBy
        isbns = [
            identified_by.get("value")
            for identified_by in record.get("identifiedBy", [])
            if identified_by.get("type") == "bf:Isbn" and identified_by.get("value")
        ]

        if not isbns:
            return False

        # Try to get thumbnail URL for the first ISBN
        for isbn in sorted(isbns):
            try:
                url, provider = get_thumbnail_url(isbn, cached=self.cached)
            except Exception as e:
                current_app.logger.warning(f"Thumbnail lookup failed for ISBN {isbn}: {e}")
                continue
            if url:
                # Add to electronicLocator
                record["electronicLocator"] = record.get("electronicLocator", [])
                locator = {"type": "relatedResource", "content": "coverImage", "url": url}
                if provider:
                    locator["note"] = f"rero-invenio-thumbnails provider: {provider}"
                record["electronicLocator"].append(locator)
                return True
        return False

    def pre_create(self, record):
        """Add a cover locator to the record before it is written to the database.

        Mutates the record dict in place so the cover URL is included in the
        initial database write without requiring a separate session flush.

        :param record: The document record about to be created.
        """
        self.add_cover_url(record)

    def pre_commit(self, record):
        """Add a cover locator to the record before it is committed to the database.

        Mutates the record dict in place so the cover URL is included in the
        commit write without requiring a separate session flush.

        :param record: The document record about to be committed.
        """
        self.add_cover_url(record)
