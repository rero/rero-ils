# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Documents dumpers."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper

from .indexer import IndexerDumper
from .replace_refs import ReplaceRefsContributionsDumper, ReplaceRefsEntitiesDumper
from .title import TitleDumper

__all__ = (
    "ReplaceRefsContributionsDumper",
    "ReplaceRefsEntitiesDumper",
    "TitleDumper",
)

# replace linked data
document_replace_refs_dumper = MultiDumper(
    dumpers=[
        # make a fresh copy
        Dumper(),
        ReplaceRefsContributionsDumper(),
        ReplaceRefsEntitiesDumper("subjects", "genreForm"),
        ReplaceRefsDumper(),
    ]
)

# create a string version of the complex title field
document_title_dumper = MultiDumper(
    dumpers=[
        # make a fresh copy
        Dumper(),
        TitleDumper(),
    ]
)

# dumper used for indexing
document_indexer_dumper = MultiDumper(
    dumpers=[
        # make a fresh copy
        Dumper(),
        ReplaceRefsContributionsDumper(),
        ReplaceRefsEntitiesDumper("subjects", "genreForm"),
        ReplaceRefsDumper(),
        IndexerDumper(),
    ]
)
