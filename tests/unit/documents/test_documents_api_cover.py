# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for Document.cover property — no database required."""

from rero_ils.modules.documents.api import Document

URL = "https://example.com/cover.jpg"
PROVIDER = "acme"


class _StubDocument(dict):
    """Minimal dict subclass that exposes the cover property."""


_StubDocument.cover = Document.cover


def test_cover_returns_none_when_no_locators():
    doc = _StubDocument()
    assert doc.cover == (None, None)


def test_cover_returns_none_when_no_cover_image():
    doc = _StubDocument()
    doc["electronicLocator"] = [{"content": "fullText", "type": "resource", "url": "https://example.com/full.pdf"}]
    assert doc.cover == (None, None)


def test_cover_returns_url_and_provider():
    doc = _StubDocument()
    doc["electronicLocator"] = [
        {
            "content": "coverImage",
            "type": "relatedResource",
            "url": URL,
            "publicNote": [f"rero-invenio-thumbnails provider: {PROVIDER}"],
        }
    ]
    url, provider = doc.cover
    assert url == URL
    assert provider == PROVIDER


def test_cover_returns_url_without_provider():
    doc = _StubDocument()
    doc["electronicLocator"] = [{"content": "coverImage", "type": "relatedResource", "url": URL}]
    url, provider = doc.cover
    assert url == URL
    assert provider is None


def test_cover_ignores_non_related_resource():
    doc = _StubDocument()
    doc["electronicLocator"] = [{"content": "coverImage", "type": "resource", "url": URL}]
    assert doc.cover == (None, None)
