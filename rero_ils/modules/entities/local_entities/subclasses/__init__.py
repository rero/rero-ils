# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity record subclasses."""

from .organisation import OrganisationLocalEntity
from .person import PersonLocalEntity
from .place import PlaceLocalEntity
from .temporal import TemporalLocalEntity
from .topic import TopicLocalEntity
from .work import WorkLocalEntity

__all__ = [
    "OrganisationLocalEntity",
    "PersonLocalEntity",
    "PlaceLocalEntity",
    "TemporalLocalEntity",
    "TopicLocalEntity",
    "WorkLocalEntity",
]
