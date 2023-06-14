# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
        from ..subclasses import OrganisationLocalEntity, PersonLocalEntity, \
            PlaceLocalEntity, TemporalLocalEntity, TopicLocalEntity, \
            WorkLocalEntity

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
