# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Entities model class."""


class EntityType:
    """Class holding all available entity types."""

    AGENT = "bf:Agent"
    ORGANISATION = "bf:Organisation"
    PERSON = "bf:Person"
    PLACE = "bf:Place"
    TEMPORAL = "bf:Temporal"
    TOPIC = "bf:Topic"
    WORK = "bf:Work"


class EntityResourceType:
    """Class holding all available resource entity types."""

    REMOTE = "remote"
    LOCAL = "local"


class EntityFieldWithRef:
    """Class to define field with $ref."""

    CONTRIBUTION = "contribution"
    GENRE_FORM = "genreForm"
    SUBJECTS = "subjects"
