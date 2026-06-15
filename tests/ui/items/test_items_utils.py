# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Items Record utils tests."""

import pytest

from rero_ils.modules.items.utils import exists_available_item


def test_exists_available_item(item_lib_martigny):
    """Test exists_available_items function."""
    assert not exists_available_item([])
    assert exists_available_item([item_lib_martigny])
    assert exists_available_item([item_lib_martigny.pid])

    with pytest.raises(ValueError):
        assert exists_available_item([0, item_lib_martigny.pid])
