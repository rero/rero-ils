# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common entity dumpers."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper

from .authorized_acces_point import LocalizedAuthorizedAccessPointDumper
from .document import BaseDocumentEntityDumper
from .indexer import EntityIndexerDumper

# replace linked data (seems not necessary at this time)
replace_refs_dumper = MultiDumper(
    dumpers=[
        # make a fresh copy
        Dumper(),
        ReplaceRefsDumper(),
    ]
)

# dumper used for indexing
indexer_dumper = MultiDumper(
    dumpers=[
        # make a fresh copy
        Dumper(),
        ReplaceRefsDumper(),
        EntityIndexerDumper(),
        LocalizedAuthorizedAccessPointDumper(),
    ]
)

document_dumper = MultiDumper(
    dumpers=[
        BaseDocumentEntityDumper(),
        EntityIndexerDumper(),
        LocalizedAuthorizedAccessPointDumper(),
    ]
)
