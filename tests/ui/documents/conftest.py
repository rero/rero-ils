# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest item_types."""

import pytest


@pytest.fixture(scope="module")
def document_records(document, document_ref, document_sion_items, ebook_1, ebook_2, ebook_3):
    """Documents for test mapping."""
