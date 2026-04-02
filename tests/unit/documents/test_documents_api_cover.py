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
