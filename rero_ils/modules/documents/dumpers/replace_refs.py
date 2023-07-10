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

"""Replace refs dumpers."""
from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.exceptions import RecordNotFound
from rero_ils.modules.entities.dumpers import document_dumper
from rero_ils.modules.entities.remote_entities.utils import \
    extract_data_from_mef_uri
from rero_ils.modules.utils import extracted_data_from_ref


class ReplaceRefsEntitiesDumperMixin(Dumper):
    """Mixin class for entity dumper."""

    @staticmethod
    def _replace_entity(data):
        """Replace the `$ref` linked contributions."""
        from rero_ils.modules.entities.local_entities.api import LocalEntity
        from rero_ils.modules.entities.remote_entities.api import RemoteEntity

        # try to get entity record
        entity = extracted_data_from_ref(data['$ref'], 'record')
        # check if local entity
        if entity and isinstance(entity, LocalEntity):
            # internal resources will be resolved later (see ReplaceRefsDumper)
            return entity.dumps(document_dumper)

        _, _type, _ = extract_data_from_mef_uri(data['$ref'])
        if not (entity := RemoteEntity.get_record_by_pid(data['pid'])):
            raise RecordNotFound(RemoteEntity, data['pid'])

        entity = entity.dumps(document_dumper)
        entity.update({
            'primary_source': _type,
            'pid': data['pid']
        })
        return entity


class ReplaceRefsContributionsDumper(ReplaceRefsEntitiesDumperMixin):
    """Replace linked contributions in document."""

    def dump(self, record, data):
        """Dump an item instance for notification.

        :param record: record to dump.
        :param data: initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        new_contributions = []
        for contribution in data.get('contribution', []):
            if contribution['entity'].get('$ref'):
                new_contributions.append({
                    'entity': self._replace_entity(contribution['entity']),
                    'role': contribution['role']
                })
            else:
                new_contributions.append(contribution)
        if new_contributions:
            data['contribution'] = new_contributions
        return data


class ReplaceRefsEntitiesDumper(ReplaceRefsEntitiesDumperMixin):
    """Replace linked entities in document."""

    def __init__(self, *args):
        """Initialization.

        :param args: field names on which replace the $ref entities.
        :type args: tuple<str>
        """
        self.field_names = list(args) or []

    def dump(self, record, data):
        """Dump record data by replacing linked subjects and imported subjects.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        for field_name in self.field_names:
            remote_entities = []
            for entity in [d['entity'] for d in data.get(field_name, [])]:
                if entity.get('$ref'):
                    entity = self._replace_entity(entity)
                remote_entities.append({'entity': entity})
            if remote_entities:
                data[field_name] = remote_entities
        return data
