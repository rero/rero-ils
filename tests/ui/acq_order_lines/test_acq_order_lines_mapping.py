# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition order line Record mapping tests."""

from rero_ils.modules.acquisition.acq_order_lines.api import (
    AcqOrderLine,
    AcqOrderLinesSearch,
)
from tests.utils import get_mapping


def test_acq_order_lines_search_mapping(
    es,
    db,
    document,
    acq_account_fiction_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny_data,
):
    """Test aquisition order line search index mapping."""
    search = AcqOrderLinesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    acq_line = AcqOrderLine.create(
        acq_order_line_fiction_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True,
    )
    assert mapping == get_mapping(search.Meta.index)
    acq_line.delete(force=True, dbcommit=True, delindex=True)
