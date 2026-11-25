# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document dumpers unit tests."""

import pytest

from rero_ils.modules.documents.dumpers.indexer import IndexerDumper


@pytest.mark.parametrize(
    ("physical_holdings", "expected"),
    [
        pytest.param([], (False, False), id="no-holding"),
        pytest.param([("physical", [])], (False, True), id="empty-physical-holding"),
        pytest.param([("online", [])], (False, False), id="empty-online-holding"),
        pytest.param([("physical", [None])], (False, True), id="physical-item"),
        pytest.param([("online", [None])], (True, False), id="online-holding-item"),
        pytest.param([("physical", ["online"])], (True, False), id="online-temporary-location"),
        pytest.param([("online", ["physical"])], (True, False), id="online-holding-physical-temporary"),
        pytest.param([("physical", [None, "online"])], (True, True), id="mixed-items"),
        pytest.param([("physical", [None]), ("online", [None])], (True, True), id="mixed-holdings"),
    ],
)
def test_resource_flags(physical_holdings, expected):
    """Classify items by their holding location and temporary location."""
    assert IndexerDumper._resource_flags(physical_holdings, {"online"}) == expected
