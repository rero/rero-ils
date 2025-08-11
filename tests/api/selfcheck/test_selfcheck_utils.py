# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

"""Tests Selfcheck api."""

from rero_ils.modules.items.models import ItemIssueStatus, ItemStatus
from rero_ils.modules.selfcheck.utils import map_item_circulation_status, map_media_type


def test_media_type(client):
    """Test invenio-sip2 media type mapping."""
    # TODO: test all document types
    assert map_media_type("docmaintype_book") == "BOOK"
    assert map_media_type("docmaintype_article") == "MAGAZINE"
    assert map_media_type("docmaintype_serial") == "MAGAZINE"
    assert map_media_type("docmaintype_series") == "BOUND_JOURNAL"
    assert map_media_type("docmaintype_audio") == "AUDIO"
    assert map_media_type("docmaintype_movie_series") == "VIDEO"


def test_circulation_status():
    """Test invenio-sip2 item circultation status mapping."""
    assert map_item_circulation_status(ItemStatus.ON_SHELF) == "AVAILABLE"
    assert map_item_circulation_status(ItemStatus.AT_DESK) == "WAITING_ON_HOLD_SHELF"
    assert map_item_circulation_status(ItemStatus.ON_LOAN) == "CHARGED"
    assert map_item_circulation_status(ItemStatus.IN_TRANSIT) == "IN_TRANSIT"
    assert map_item_circulation_status(ItemStatus.MISSING) == "MISSING"
    assert map_item_circulation_status(ItemStatus.EXCLUDED) == "OTHER"
    assert map_item_circulation_status(ItemIssueStatus.RECEIVED) == "OTHER"
    assert map_item_circulation_status(ItemIssueStatus.DELETED) == "OTHER"
    assert map_item_circulation_status(ItemIssueStatus.LATE) == "OTHER"
