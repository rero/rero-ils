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

from rero_ils.modules.documents.tasks import add_cover_urls, enqueue_cover_url_update, process_cover_url_queue


def _make_hit(pid):
    hit = mock.MagicMock()
    hit.pid = pid
    return hit


def _make_document(pid, cover=(None, None)):
    """Create a mock document with a configurable cover property."""
    doc = mock.MagicMock()
    doc.pid = pid
    type(doc).cover = mock.PropertyMock(return_value=cover)
    return doc


def _setup_scan(mock_search, hits):
    """Wire the DocumentsSearch mock chain to return the given hits from scan()."""
    (
        mock_search.return_value.filter.return_value.exclude.return_value.params.return_value.source.return_value.scan.return_value
    ) = hits


@pytest.fixture
def mock_redis():
    """Patch _cover_url_redis to return a mock Redis client."""
    r = mock.MagicMock()
    with mock.patch("rero_ils.modules.documents.tasks._cover_url_redis", return_value=r):
        yield r


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
def mock_extension_cls():
    """Patch AddCoverUrlExtension to control cover URL addition."""
    with mock.patch("rero_ils.modules.documents.extensions.add_cover_url.AddCoverUrlExtension") as m:
        yield m


@pytest.fixture
def mock_set_timestamp():
    """Suppress set_timestamp side-effects (DB write)."""
    with mock.patch("rero_ils.modules.documents.tasks.set_timestamp"):
        yield


# --- add_cover_urls (batch) ---


def test_add_cover_urls_extension_adds_cover(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp, cover_url, provider
):
    """Extension finds a cover; task counts and does not persist without commit."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", cover=(cover_url, provider))
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = True

    result = add_cover_urls(commit=False)
    assert result == {provider: 1, "all": 1}
    doc.update.assert_not_called()


def test_add_cover_urls_extension_no_cover(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp
):
    """Extension finds no cover; task counts 0."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1")
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = False

    result = add_cover_urls(commit=False)
    assert result == {"all": 0}


def test_add_cover_urls_commit_calls_update(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp, cover_url, provider
):
    """Commit mode persists the document with update after extension adds cover."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", cover=(cover_url, provider))
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = True

    result = add_cover_urls(commit=True)
    assert result == {provider: 1, "all": 1}
    doc.update.assert_called_once_with(data=doc, commit=True, dbcommit=True, reindex=True)


def test_add_cover_urls_commit_no_cover(appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp):
    """Commit mode does not persist when extension didn't add a cover."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1")
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = False

    result = add_cover_urls(commit=True)
    assert result == {"all": 0}
    doc.update.assert_not_called()


def test_add_cover_urls_multiple_documents(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp, cover_url, provider
):
    """Task processes multiple documents and returns the total updated count."""
    _setup_scan(mock_search, [_make_hit("1"), _make_hit("2")])
    doc1 = _make_document("1", cover=(cover_url, provider))
    doc2 = _make_document("2", cover=(cover_url, provider))
    mock_document_cls.get_record_by_pid.side_effect = [doc1, doc2]
    mock_extension_cls.return_value.add_cover_url.return_value = True

    result = add_cover_urls(commit=True)
    assert result == {provider: 2, "all": 2}


def test_add_cover_urls_commit_logs_on_update_error(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp, cover_url, provider
):
    """Commit mode logs exception and continues when document update fails."""
    _setup_scan(mock_search, [_make_hit("1"), _make_hit("2")])
    doc1 = _make_document("1", cover=(cover_url, provider))
    doc1.update.side_effect = Exception("db error")
    doc2 = _make_document("2", cover=(cover_url, provider))
    mock_document_cls.get_record_by_pid.side_effect = [doc1, doc2]
    mock_extension_cls.return_value.add_cover_url.return_value = True

    result = add_cover_urls(commit=True)
    # Both documents counted even though doc1 update failed
    assert result == {provider: 2, "all": 2}
    doc2.update.assert_called_once_with(data=doc2, commit=True, dbcommit=True, reindex=True)


# --- verbose output ---


def test_verbose_with_provider(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp, cover_url
):
    """Verbose mode displays URL and provider."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", cover=(cover_url, "acme"))
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = True

    with mock.patch("rero_ils.modules.documents.tasks.click.echo") as mock_echo:
        add_cover_urls(commit=False, verbose=True)

    mock_echo.assert_called_once()
    output = mock_echo.call_args[0][0]
    assert "acme" in output
    assert cover_url in output


def test_verbose_with_provider_none(
    appctx, mock_search, mock_document_cls, mock_extension_cls, mock_set_timestamp, cover_url
):
    """Verbose mode does not raise TypeError when provider is None."""
    _setup_scan(mock_search, [_make_hit("1")])
    doc = _make_document("1", cover=(cover_url, None))
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = True

    with mock.patch("rero_ils.modules.documents.tasks.click.echo") as mock_echo:
        add_cover_urls(commit=False, verbose=True)

    mock_echo.assert_called_once()
    output = mock_echo.call_args[0][0]
    assert cover_url in output


# --- enqueue_cover_url_update ---


def test_enqueue_adds_pid_to_queue(appctx, mock_redis):
    """enqueue_cover_url_update adds the PID to the Redis queue set."""
    mock_redis.exists.return_value = False  # not paused
    mock_redis.set.return_value = None  # worker already running
    enqueue_cover_url_update("doc1")
    mock_redis.sadd.assert_called_once_with("rero_ils:cover_url_queue", "doc1")


def test_enqueue_starts_worker_when_lock_acquired(appctx, mock_redis):
    """enqueue_cover_url_update starts the worker task when no worker is running."""
    mock_redis.exists.return_value = False  # not paused
    mock_redis.set.return_value = True  # lock acquired
    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        enqueue_cover_url_update("doc1")
    mock_task.apply_async.assert_called_once()


def test_enqueue_skips_worker_when_already_running(appctx, mock_redis):
    """enqueue_cover_url_update does not start a second worker when one is running."""
    mock_redis.exists.return_value = False  # not paused
    mock_redis.set.return_value = None  # lock not acquired (worker running)
    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        enqueue_cover_url_update("doc1")
    mock_task.apply_async.assert_not_called()


def test_enqueue_skips_worker_when_paused(appctx, mock_redis):
    """enqueue_cover_url_update still adds the PID but does not start a worker when paused."""
    mock_redis.exists.return_value = True  # paused
    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        enqueue_cover_url_update("doc1")
    mock_redis.sadd.assert_called_once_with("rero_ils:cover_url_queue", "doc1")
    mock_task.apply_async.assert_not_called()


# --- process_cover_url_queue ---


def test_process_queue_processes_pid_and_reschedules(
    appctx, mock_redis, mock_document_cls, mock_extension_cls, cover_url, provider
):
    """process_cover_url_queue pops a PID, adds cover, updates document, and reschedules."""
    mock_redis.spop.return_value = b"doc1"
    doc = _make_document("doc1", cover=(cover_url, provider))
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = True

    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        process_cover_url_queue()

    doc.update.assert_called_once_with(data=doc, commit=True, dbcommit=True, reindex=True)
    mock_task.apply_async.assert_called_once()


def test_process_queue_logs_and_continues_on_update_error(
    appctx, mock_redis, mock_document_cls, mock_extension_cls, cover_url, provider
):
    """process_cover_url_queue logs the exception and still reschedules when update fails."""
    mock_redis.spop.return_value = b"doc1"
    doc = _make_document("doc1", cover=(cover_url, provider))
    doc.update.side_effect = Exception("db error")
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = True

    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        process_cover_url_queue()

    mock_task.apply_async.assert_called_once()


def test_process_queue_skips_update_when_no_cover_found(appctx, mock_redis, mock_document_cls, mock_extension_cls):
    """process_cover_url_queue does not call update when extension finds no cover."""
    mock_redis.spop.return_value = b"doc1"
    doc = _make_document("doc1")
    mock_document_cls.get_record_by_pid.return_value = doc
    mock_extension_cls.return_value.add_cover_url.return_value = False

    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        process_cover_url_queue()

    doc.update.assert_not_called()
    mock_task.apply_async.assert_called_once()


def test_process_queue_skips_when_document_not_found(appctx, mock_redis, mock_document_cls):
    """process_cover_url_queue reschedules even when the document PID is not found."""
    mock_redis.spop.return_value = b"missing-pid"
    mock_document_cls.get_record_by_pid.return_value = None

    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        process_cover_url_queue()

    mock_task.apply_async.assert_called_once()


def test_process_queue_releases_lock_when_empty(appctx, mock_redis):
    """process_cover_url_queue deletes the worker lock when queue is empty."""
    mock_redis.spop.return_value = None
    mock_redis.scard.return_value = 0

    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        process_cover_url_queue()

    mock_redis.delete.assert_called_once()
    mock_task.apply_async.assert_not_called()


def test_process_queue_restarts_when_new_items_after_drain(appctx, mock_redis):
    """process_cover_url_queue restarts itself when new items appeared concurrently."""
    mock_redis.spop.return_value = None
    mock_redis.scard.return_value = 1  # new items added while draining
    mock_redis.set.return_value = True  # lock re-acquired

    with mock.patch("rero_ils.modules.documents.tasks.process_cover_url_queue") as mock_task:
        process_cover_url_queue()

    mock_task.apply_async.assert_called_once()
