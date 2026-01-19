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

"""Tests for AddCoverUrlExtension."""

from unittest import mock

from rero_ils.modules.documents.extensions.add_cover_url import AddCoverUrlExtension


def test_add_cover_url_extension_with_isbn(app, thumbnail_covers, cover_url):
    """Test extension adds cover URL when ISBN is present."""
    thumbnail_covers["9781234567890"] = cover_url
    extension = AddCoverUrlExtension(cached=False)
    document = {"pid": "doc1", "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}]}

    result = extension.add_cover_url(document)

    assert result is True
    assert len(document["electronicLocator"]) == 1
    locator = document["electronicLocator"][0]
    assert locator["type"] == "relatedResource"
    assert locator["content"] == "coverImage"
    assert locator["url"] == cover_url
    assert locator["note"] == "rero-invenio-thumbnails provider: test"


def test_add_cover_url_extension_without_isbn(app, thumbnail_covers):
    """Test extension does nothing when no ISBN is present."""
    extension = AddCoverUrlExtension(cached=False)
    document = {"pid": "doc1", "identifiedBy": [{"type": "bf:Issn", "value": "1234-5678"}]}

    result = extension.add_cover_url(document)

    assert result is False
    assert "electronicLocator" not in document


def test_add_cover_url_extension_already_has_cover(app, thumbnail_covers, cover_url):
    """Test extension does nothing when a coverImage locator already exists."""
    thumbnail_covers["9781234567890"] = cover_url
    extension = AddCoverUrlExtension(cached=False)
    document = {
        "pid": "doc1",
        "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}],
        "electronicLocator": [
            {"type": "relatedResource", "content": "coverImage", "url": "https://existing.example.com/cover.jpg"}
        ],
    }

    result = extension.add_cover_url(document)

    assert result is False
    assert len(document["electronicLocator"]) == 1
    assert document["electronicLocator"][0]["url"] == "https://existing.example.com/cover.jpg"


def test_add_cover_url_extension_multiple_isbns(app, thumbnail_covers, cover_url):
    """Test extension uses first successful ISBN in sorted order."""
    # Only the second sorted ISBN ("9781234567890") has a cover
    thumbnail_covers["9781234567890"] = cover_url
    extension = AddCoverUrlExtension(cached=False)
    document = {
        "pid": "doc1",
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9780000000000"},
            {"type": "bf:Isbn", "value": "9781234567890"},
            {"type": "bf:Isbn", "value": "9789999999999"},
        ],
    }

    result = extension.add_cover_url(document)

    assert result is True
    assert len(document["electronicLocator"]) == 1
    assert document["electronicLocator"][0]["url"] == cover_url


def test_add_cover_url_extension_no_thumbnail_available(app, thumbnail_covers):
    """Test extension does nothing when no thumbnail is available for any ISBN."""
    # covers is empty — TestThumbnailProvider returns (None, "test") for all ISBNs
    extension = AddCoverUrlExtension(cached=False)
    document = {"pid": "doc1", "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}]}

    result = extension.add_cover_url(document)

    assert result is False
    assert "electronicLocator" not in document


def test_add_cover_url_extension_cached_parameter(app, thumbnail_covers, cover_url):
    """Test extension works correctly with cached=False."""
    thumbnail_covers["9781234567890"] = cover_url
    extension = AddCoverUrlExtension(cached=False)
    document = {"pid": "doc1", "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}]}

    result = extension.add_cover_url(document)

    assert result is True
    assert document["electronicLocator"][0]["url"] == cover_url


def test_add_cover_url_extension_preserves_existing_locators(app, thumbnail_covers, cover_url):
    """Test extension preserves existing non-cover electronicLocators."""
    thumbnail_covers["9781234567890"] = cover_url
    extension = AddCoverUrlExtension(cached=False)
    document = {
        "pid": "doc1",
        "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}],
        "electronicLocator": [{"type": "resource", "content": "fullText", "url": "https://example.com/fulltext.pdf"}],
    }

    extension.add_cover_url(document)

    assert len(document["electronicLocator"]) == 2
    assert document["electronicLocator"][0]["content"] == "fullText"
    assert document["electronicLocator"][1]["content"] == "coverImage"


def test_add_cover_url_extension_sorted_isbns(app, thumbnail_covers, cover_url):
    """Test extension uses the first (smallest) ISBN that has a cover."""
    # Only the smallest sorted ISBN has a cover — verifies sorted-order processing
    thumbnail_covers["9780000000000"] = cover_url
    extension = AddCoverUrlExtension(cached=False)
    document = {
        "pid": "doc1",
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9789999999999"},
            {"type": "bf:Isbn", "value": "9780000000000"},
            {"type": "bf:Isbn", "value": "9781234567890"},
        ],
    }

    extension.add_cover_url(document)

    assert document["electronicLocator"][0]["url"] == cover_url


def test_add_cover_url_extension_exception_then_success(app, cover_url):
    """Test extension continues to next ISBN after get_thumbnail_url raises."""
    extension = AddCoverUrlExtension(cached=False)
    document = {
        "pid": "doc1",
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9781111111111"},
            {"type": "bf:Isbn", "value": "9782222222222"},
        ],
    }

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.get_thumbnail_url") as mock_get:
        mock_get.side_effect = [
            RuntimeError("service unavailable"),
            (cover_url, "test"),
        ]

        result = extension.add_cover_url(document)

    assert result is True
    assert document["electronicLocator"][0]["url"] == cover_url
    assert mock_get.call_count == 2
