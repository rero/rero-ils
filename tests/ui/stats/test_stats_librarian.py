# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2023 UCL
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

"""Stats Librarian tests."""

import mock
from invenio_db import db
from utils import flush_index

from rero_ils.modules.documents.api import Document
from rero_ils.modules.loans.logs.api import LoanOperationLog
from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.stats.api.librarian import StatsForLibrarian


def test_stats_librarian_collect(stat_for_librarian):
    """Test the stat librarian collect keys."""

    assert list(stat_for_librarian.collect()[0].keys()) == [
        'library', 'checkouts_for_transaction_library',
        'checkouts_for_owning_library', 'active_patrons_by_postal_code',
        'new_active_patrons_by_postal_code', 'new_documents', 'new_items',
        'renewals', 'validated_requests', 'items_by_document_type_and_subtype',
        'new_items_by_location',
        'loans_of_transaction_library_by_item_location'
    ]


def test_stats_librarian_checkouts_for_transaction_library(
        stat_for_librarian, loan_due_soon_martigny, lib_martigny, lib_sion):
    """Test the number of circulation operation during the specified timeframe.
    """
    assert stat_for_librarian\
        .checkouts_for_transaction_library('foo') == 0
    assert stat_for_librarian\
        .checkouts_for_transaction_library(lib_sion.pid) == 0
    assert stat_for_librarian\
        .checkouts_for_transaction_library(lib_martigny.pid) == 1


def test_stats_librarian_checkouts_for_owning_library(
        stat_for_librarian, loan_due_soon_martigny, lib_martigny, lib_sion):
    """Test the number of circulation operation during the specified timeframe.
    """
    assert stat_for_librarian\
        .checkouts_for_owning_library('foo') == 0
    assert stat_for_librarian\
        .checkouts_for_owning_library(lib_sion.pid) == 0
    assert stat_for_librarian\
        .checkouts_for_owning_library(lib_martigny.pid) == 1


def test_stats_librarian_active_patrons_by_postal_code(
        stat_for_librarian, loan_due_soon_martigny, lib_martigny):
    """Test the number of circulation operation during the specified timeframe.
    """
    assert stat_for_librarian\
        .active_patrons_by_postal_code('foo') == {}
    assert stat_for_librarian\
        .active_patrons_by_postal_code(lib_martigny.pid) == {'1920': 1}

    # with new patrons
    assert stat_for_librarian\
        .active_patrons_by_postal_code('foo', new_patrons=True) == {}
    assert stat_for_librarian\
        .active_patrons_by_postal_code(
            lib_martigny.pid, new_patrons=True) == {'1920': 1}
    stat = StatsForLibrarian()
    assert stat\
        .active_patrons_by_postal_code(
            lib_martigny.pid, new_patrons=True) == {}


def test_stats_librarian_new_documents(
        stat_for_librarian, document_data, lib_martigny, librarian_martigny):
    """Test the number of new documents per library for given time interval."""
    assert stat_for_librarian.new_documents('foo') == 0
    with mock.patch(
        'rero_ils.modules.operation_logs.extensions.current_librarian',
        librarian_martigny
    ):
        # needs to create a new document created by a librarian
        Document.create(
            data=document_data, delete_pid=True, dbcommit=False, reindex=False)
        flush_index(OperationLog.index_name)

        assert stat_for_librarian.new_documents(lib_martigny.pid) == 1
        stat = StatsForLibrarian()
        assert stat.new_documents(lib_martigny.pid) == 0
        db.session.rollback()


def test_stats_librarian_renewals(
        stat_for_librarian, lib_martigny, loan_due_soon_martigny,
        loc_public_martigny, librarian_martigny):
    """Test the number of items with loan extended."""
    assert stat_for_librarian.renewals('foo') == 0
    loan_due_soon_martigny.item.extend_loan(
        pid=loan_due_soon_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid
    )
    flush_index(LoanOperationLog.index_name)
    assert stat_for_librarian.renewals(lib_martigny.pid) == 1


def test_stats_librarian_validated_requests(
        stat_for_librarian, lib_sion, loan_validated_sion):
    """Test the number of validated requests."""
    assert stat_for_librarian.validated_requests('foo') == 0
    assert stat_for_librarian.validated_requests(lib_sion.pid) == 1


def test_stats_librarian_new_items_by_location(
        stat_for_librarian, item_lib_martigny, loc_public_martigny):
    """Test the number of new items per library by location."""
    loc = loc_public_martigny
    assert stat_for_librarian.new_items_by_location('foo') == {}
    assert stat_for_librarian.new_items_by_location(
        item_lib_martigny.library_pid)[f'{loc["code"]} - {loc["name"]}'] >= 1
    stat = StatsForLibrarian()
    assert stat.new_items_by_location(item_lib_martigny.library_pid) == {}


def test_stats_librarian_items_by_document_type_and_subtype(
        stat_for_librarian, item_lib_martigny, loc_public_martigny):
    """Test the number of items per library by document type and sub-type."""
    loc = loc_public_martigny
    assert stat_for_librarian.items_by_document_type_and_subtype('foo') == {}
    assert stat_for_librarian.items_by_document_type_and_subtype(
        item_lib_martigny.library_pid)['docmaintype_book'] >= 1
    assert stat_for_librarian.items_by_document_type_and_subtype(
        item_lib_martigny.library_pid)['docsubtype_other_book'] >= 1


def test_stats_librarian_loans_of_transaction_library_by_item_location(
        stat_for_librarian, loan_due_soon_martigny, lib_martigny,
        loc_public_martigny):
    """Test the number of circulation operation during the specified timeframe.
    """
    assert stat_for_librarian\
        .loans_of_transaction_library_by_item_location('foo') == {}
    key = f'{lib_martigny.pid}: {lib_martigny["name"]} -'\
          f' {loc_public_martigny["name"]}'
    res = stat_for_librarian\
        .loans_of_transaction_library_by_item_location(lib_martigny.pid)
    assert res[key]['checkin'] == 0
    assert res[key]['checkout'] >= 0
