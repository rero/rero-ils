# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""MARC21 RERO to JSON."""

from .dnb.model import marc21 as marc21_dnb
from .kul.model import marc21 as marc21_kul
from .loc.model import marc21 as marc21_loc
from .rero.model import marc21 as marc21_rero
from .slsp.model import marc21 as marc21_slsp
from .ugent.model import marc21 as marc21_ugent

__all__ = (
    "marc21_dnb",
    "marc21_kul",
    "marc21_loc",
    "marc21_rero",
    "marc21_slsp",
    "marc21_ugent",
)
