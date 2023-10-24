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

"""Stats Pricing tests."""

import mock
from invenio_db import db
from utils import flush_index

from rero_ils.modules.ill_requests.models import ILLRequestStatus
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.loans.logs.api import LoanOperationLog
from rero_ils.modules.stats.api.pricing import StatsForPricing


def test_stats_pricing_collect(stat_for_pricing):
    """Test the stat pricing collect keys."""

    assert list(stat_for_pricing.collect()[0].keys()) == [
        'library', 'number_of_documents', 'number_of_libraries',
        'number_of_librarians', 'number_of_active_patrons',
        'number_of_order_lines', 'number_of_checkouts', 'number_of_renewals',
        'number_of_ill_requests', 'number_of_items',
        'number_of_new_items', 'number_of_deleted_items', 'number_of_patrons',
        'number_of_new_patrons', 'number_of_checkins', 'number_of_requests']


def test_stats_pricing_number_of_documents(
        stat_for_pricing, item_lib_martigny):
    """Test the number of documents linked to my library."""
    assert stat_for_pricing.number_of_documents('foo') == 0
    assert stat_for_pricing\
        .number_of_documents(item_lib_martigny.library_pid) == 1


def test_stats_pricing_number_of_libraries(stat_for_pricing, lib_martigny):
    """Test the Number of libraries of the given organisation."""
    assert stat_for_pricing.number_of_libraries('foo') == 0
    assert stat_for_pricing\
        .number_of_libraries(lib_martigny.organisation_pid) == 1


def test_stats_pricing_number_of_librarians(
        stat_for_pricing, librarian_martigny):
    """Test the number of users with a librarian role."""
    assert stat_for_pricing.number_of_librarians('foo') == 0
    lib_pid = librarian_martigny.replace_refs()['libraries'][0]['pid']
    assert stat_for_pricing.number_of_librarians(lib_pid) == 1


def test_stats_pricing_number_of_active_patrons(
        stat_for_pricing, loan_due_soon_martigny, lib_martigny):
    """Test the number of patrons who did a transaction in the past 365 days.
    """
    assert stat_for_pricing.number_of_active_patrons('foo') == 0
    assert stat_for_pricing.number_of_active_patrons(lib_martigny.pid) == 1


def test_stats_pricing_number_of_order_lines(
        stat_for_pricing, acq_order_line_fiction_martigny):
    """Test the number of order lines created during the specified timeframe.
    """
    assert stat_for_pricing.number_of_order_lines('foo') == 0
    lib_pid = acq_order_line_fiction_martigny.library_pid
    assert stat_for_pricing.number_of_order_lines(lib_pid) == 1


def test_stats_pricing_number_of_circ_operations(
        stat_for_pricing, loan_due_soon_martigny, lib_martigny):
    """Test the number of circulation operation  during the specified
       timeframe.
    """
    assert stat_for_pricing\
        .number_of_circ_operations('foo', ItemCirculationAction.CHECKOUT) == 0
    assert stat_for_pricing\
        .number_of_circ_operations(
            lib_martigny.pid, ItemCirculationAction.EXTEND) == 0
    assert stat_for_pricing\
        .number_of_circ_operations(
            lib_martigny.pid, ItemCirculationAction.CHECKOUT) == 1


def test_stats_pricing_number_of_ill_requests(
        stat_for_pricing, ill_request_martigny, lib_martigny):
    """Test the number of ILL requests."""
    assert stat_for_pricing\
        .number_of_ill_requests(
            'foo', [ILLRequestStatus.DENIED]) == 0
    lib_pid = lib_martigny.pid
    assert stat_for_pricing\
        .number_of_ill_requests(
            lib_pid, [ILLRequestStatus.DENIED]) == 1
    assert stat_for_pricing\
        .number_of_ill_requests(
            lib_pid, [ILLRequestStatus.PENDING]) == 0


def test_stats_pricing_number_of_items(
        stat_for_pricing, item_lib_martigny):
    """Test the number of items linked to my library."""
    assert stat_for_pricing.number_of_items('foo') == 0
    # loans used in previous tests can adds some items
    assert stat_for_pricing\
        .number_of_items(item_lib_martigny.library_pid) >= 1


def test_stats_pricing_number_of_new_items(
        stat_for_pricing, item_lib_martigny):
    """Test the number of new created items during the specified timeframe."""
    assert stat_for_pricing.number_of_new_items('foo') == 0
    # loans used in previous tests can adds some items
    assert stat_for_pricing\
        .number_of_new_items(item_lib_martigny.library_pid) >= 1
    from rero_ils.modules.stats.api.pricing import StatsForPricing

    # today item creation is excluded
    stat = StatsForPricing()
    assert stat\
        .number_of_new_items(item_lib_martigny.library_pid) == 0


def test_stats_pricing_number_of_deleted_items(
        stat_for_pricing, item_lib_martigny, librarian_martigny):
    """Test the number of deleted items during the specified timeframe."""
    assert stat_for_pricing.number_of_deleted_items('foo') == 0
    with mock.patch(
        'rero_ils.modules.operation_logs.extensions.current_librarian',
        librarian_martigny
    ):
        item_lib_martigny.delete(False, False, False)
        flush_index(LoanOperationLog.index_name)
        assert stat_for_pricing\
            .number_of_deleted_items(item_lib_martigny.library_pid) == 1
        db.session.rollback()


def test_stats_pricing_number_of_patrons(
        stat_for_pricing, patron_martigny):
    """Test the number of users with a librarian role."""
    assert stat_for_pricing.number_of_patrons('foo') == 0
    # loans used in previous tests can adds some items
    assert stat_for_pricing\
        .number_of_patrons(patron_martigny.organisation_pid) >= 1


def test_stats_pricing_number_of_new_patrons(
        stat_for_pricing, patron_martigny):
    """Test the number of new patrons for an organisation during the specified
       timeframe.
    """
    assert stat_for_pricing.number_of_patrons('foo') == 0
    # loans used in previous tests can adds some items
    assert stat_for_pricing\
        .number_of_patrons(patron_martigny.organisation_pid) >= 1
    # today item creation is excluded
    stat = StatsForPricing()
    assert stat\
        .number_of_new_patrons(patron_martigny.organisation_pid) == 0
