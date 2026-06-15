# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for AddCoverUrlExtension."""

from unittest import mock

from rero_ils.modules.documents.extensions.add_cover_url import AddCoverUrlExtension


def test_add_cover_url_extension_with_isbn(appctx, thumbnail_covers, cover_url):
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
    assert "rero-invenio-thumbnails provider: test" in locator["publicNote"]


def test_add_cover_url_extension_without_isbn(appctx, thumbnail_covers):
    """Test extension does nothing when no ISBN is present."""
    extension = AddCoverUrlExtension(cached=False)
    document = {"pid": "doc1", "identifiedBy": [{"type": "bf:Issn", "value": "1234-5678"}]}

    result = extension.add_cover_url(document)

    assert result is False
    assert "electronicLocator" not in document


def test_add_cover_url_extension_already_has_cover(appctx, thumbnail_covers, cover_url):
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


def test_add_cover_url_extension_multiple_isbns(appctx, thumbnail_covers, cover_url):
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


def test_add_cover_url_extension_no_thumbnail_available(appctx, thumbnail_covers):
    """Test extension does nothing when no thumbnail is available for any ISBN."""
    extension = AddCoverUrlExtension(cached=False)
    document = {"pid": "doc1", "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}]}

    result = extension.add_cover_url(document)

    assert result is False
    assert "electronicLocator" not in document


def test_add_cover_url_extension_preserves_existing_locators(appctx, thumbnail_covers, cover_url):
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


def test_add_cover_url_extension_sorted_isbns(appctx, thumbnail_covers, cover_url):
    """Test extension uses the first (smallest) ISBN that has a cover."""
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


def test_add_cover_url_extension_exception_then_success(appctx, cover_url):
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


# --- post_create / post_commit hook tests ---


def test_post_commit_enqueues_when_no_cover(appctx):
    """post_commit enqueues the PID when the record has an ISBN and no cover."""
    extension = AddCoverUrlExtension(cached=False)
    record = {"pid": "doc1", "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}]}

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.enqueue_cover_url_update") as mock_enqueue:
        extension.post_commit(record)

    mock_enqueue.assert_called_once_with("doc1", cached=False)


def test_post_commit_skips_when_has_cover(appctx, cover_url):
    """post_commit does not enqueue when the record already has a cover."""
    extension = AddCoverUrlExtension(cached=False)
    record = {
        "pid": "doc1",
        "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}],
        "electronicLocator": [{"type": "relatedResource", "content": "coverImage", "url": cover_url}],
    }

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.enqueue_cover_url_update") as mock_enqueue:
        extension.post_commit(record)

    mock_enqueue.assert_not_called()


def test_post_commit_skips_when_no_isbn(appctx):
    """post_commit does not enqueue when the record has no ISBN."""
    extension = AddCoverUrlExtension(cached=False)
    record = {"pid": "doc1", "identifiedBy": [{"type": "bf:Issn", "value": "1234-5678"}]}

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.enqueue_cover_url_update") as mock_enqueue:
        extension.post_commit(record)

    mock_enqueue.assert_not_called()


def test_post_create_enqueues_when_no_cover(appctx):
    """post_create enqueues the PID when the record has an ISBN and no cover."""
    extension = AddCoverUrlExtension(cached=False)
    record = {"pid": "doc1", "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}]}

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.enqueue_cover_url_update") as mock_enqueue:
        extension.post_create(record)

    mock_enqueue.assert_called_once_with("doc1", cached=False)


def test_post_create_skips_when_has_cover(appctx, cover_url):
    """post_create does not enqueue when the record already has a cover."""
    extension = AddCoverUrlExtension(cached=False)
    record = {
        "pid": "doc1",
        "identifiedBy": [{"type": "bf:Isbn", "value": "9781234567890"}],
        "electronicLocator": [{"type": "relatedResource", "content": "coverImage", "url": cover_url}],
    }

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.enqueue_cover_url_update") as mock_enqueue:
        extension.post_create(record)

    mock_enqueue.assert_not_called()


def test_post_create_skips_when_no_isbn(appctx):
    """post_create does not enqueue when the record has no ISBN."""
    extension = AddCoverUrlExtension(cached=False)
    record = {"pid": "doc1", "identifiedBy": [{"type": "bf:Issn", "value": "1234-5678"}]}

    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.enqueue_cover_url_update") as mock_enqueue:
        extension.post_create(record)

    mock_enqueue.assert_not_called()
