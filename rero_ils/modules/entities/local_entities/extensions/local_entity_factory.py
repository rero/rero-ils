# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity record factory extensions."""

from invenio_records.extensions import RecordExtension

from ...models import EntityType


class LocalEntityFactoryExtension(RecordExtension):
    """Local entity factory extension class.

    Choose the best local entity subclass based on `type` attributes.
    """

    @staticmethod
    def _get_local_entity_class(record):
        """Get the Local entity class to use based on record data."""
        from ..api import LocalEntity
        from ..subclasses import (
            OrganisationLocalEntity,
            PersonLocalEntity,
            PlaceLocalEntity,
            TemporalLocalEntity,
            TopicLocalEntity,
            WorkLocalEntity,
        )

        mapping = {
            EntityType.PERSON: PersonLocalEntity,
            EntityType.ORGANISATION: OrganisationLocalEntity,
            EntityType.TOPIC: TopicLocalEntity,
            EntityType.PLACE: PlaceLocalEntity,
            EntityType.TEMPORAL: TemporalLocalEntity,
            EntityType.WORK: WorkLocalEntity,
        }

        return mapping.get(record.type, LocalEntity)

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized."""
        cls = LocalEntityFactoryExtension._get_local_entity_class(record)
        record.__class__ = cls
