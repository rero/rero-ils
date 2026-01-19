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

"""Tests for the add_cover_urls Celery task."""

from unittest import mock

import pytest

from rero_ils.modules.documents.tasks import add_cover_urls


def _make_hit(pid):
    hit = mock.MagicMock()
    hit.pid = pid
    return hit


def _make_document(pid, isbns):
    identified_by = [{"type": "bf:Isbn", "value": isbn} for isbn in isbns]
    doc = mock.MagicMock()
    doc.pid = pid
    doc.get = mock.MagicMock(side_effect=lambda key, default=None: {"identifiedBy": identified_by}.get(key, default))
    doc.add_cover_url.return_value = (doc, True)
    return doc


def _setup_scan(mock_search, hits):
    """Wire the DocumentsSearch mock chain to return the given hits from scan()."""
    (
        mock_search.return_value.filter.return_value.exclude.return_value.params.return_value.source.return_value.scan.return_value
    ) = hits


@pytest.fixture
def mock_search():
    """Patch DocumentsSearch to avoid hitting Elasticsearch."""
    with mock.patch("rero_ils.modules.documents.api.DocumentsSearch") as m:
        yield m


@pytest.fixture
def mock_document_cls():
    """Patch Document to avoid hitting the database."""
    with mock.patch("rero_ils.modules.documents.api.Document") as m:
        yield m


@pytest.fixture
def mock_thumbnail():
    """Patch get_thumbnail_url to avoid external HTTP calls."""
    with mock.patch("rero_invenio_thumbnails.get_thumbnail_url") as m:
        yield m


@pytest.fixture
def mock_set_timestamp():
    """Suppress set_timestamp side-effects (DB write)."""
    with mock.patch("rero_ils.modules.utils.set_timestamp"):
        yield


def test_add_cover_urls_no_commit(
    app, mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp, cover_url, provider
):
    """Task returns 0 and does not call add_cover_url when commit=False."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", ["9781234567890"])
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_thumbnail.return_value = (cover_url, provider)

    assert add_cover_urls(commit=False) == 0
    doc.add_cover_url.assert_not_called()


def test_add_cover_urls_commit(
    app, mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp, cover_url, provider
):
    """Task commits cover URL and returns 1 for a matching document."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", ["9781234567890"])
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_thumbnail.return_value = (cover_url, provider)

    assert add_cover_urls(commit=True) == 1
    doc.add_cover_url.assert_called_once_with(url=cover_url, provider=provider, dbcommit=True, reindex=True)


def test_add_cover_urls_no_url_found(mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp):
    """Task skips document when no thumbnail URL is returned."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", ["9780000000000"])
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_thumbnail.return_value = (None, None)

    assert add_cover_urls(commit=True) == 0
    doc.add_cover_url.assert_not_called()


def test_add_cover_urls_provider_none(mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp, cover_url):
    """Task passes provider=None to add_cover_url when provider is absent."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", ["9781234567890"])
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_thumbnail.return_value = (cover_url, None)

    assert add_cover_urls(commit=True) == 1
    doc.add_cover_url.assert_called_once_with(url=cover_url, provider=None, dbcommit=True, reindex=True)


def test_add_cover_urls_isbn_exception_then_success(
    app, mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp, cover_url, provider
):
    """Task skips a failing ISBN and succeeds on the next sorted one."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", ["9781111111111", "9782222222222"])
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_thumbnail.side_effect = [RuntimeError("timeout"), (cover_url, provider)]

    assert add_cover_urls(commit=True) == 1


def test_add_cover_urls_multiple_documents(
    mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp, cover_url, provider
):
    """Task processes multiple documents and returns the total updated count."""
    _setup_scan(mock_search, [_make_hit("1"), _make_hit("2")])
    doc1 = _make_document("1", ["9781111111111"])
    doc2 = _make_document("2", ["9782222222222"])
    mock_document_cls.get_record_by_pid.side_effect = [doc1, doc2]
    mock_thumbnail.return_value = (cover_url, provider)

    assert add_cover_urls(commit=True) == 2


def test_add_cover_urls_sorted_isbns(
    mock_search, mock_document_cls, mock_thumbnail, mock_set_timestamp, cover_url, provider
):
    """Task tries ISBNs in sorted order and stops at the first successful one."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", ["9783333333333", "9781111111111", "9782222222222"])
    mock_document_cls.get_record_by_pid.return_value = doc

    results = {
        "9781111111111": (cover_url, provider),
    }
    mock_thumbnail.side_effect = lambda isbn, **_kw: results.get(isbn, (None, None))

    assert add_cover_urls(commit=True) == 1
    assert mock_thumbnail.call_args_list[0][0][0] == "9781111111111"
