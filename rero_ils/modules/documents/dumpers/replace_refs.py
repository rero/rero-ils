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

from copy import deepcopy

from invenio_records.api import _records_state
from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.exceptions import RecordNotFound
from rero_ils.modules.entities.models import EntityType


class ReplaceRefsEntitiesDumper(Dumper):
    """Replace linked contributions in document."""

    @staticmethod
    def _replace_entity(data):
        """Replace the `$ref` linked contributions."""
        from rero_ils.modules.entities.api import Entity
        if not (entity := Entity.get_record_by_pid(data['pid'])):
            raise RecordNotFound(Entity, data['pid'])
        _type, _ = Entity.get_type_and_pid_from_ref(data['$ref'])
        contribution = entity.dumps_for_document()
        contribution.update({
            'primary_source': _type,
            'pid': data['pid']
        })
        return contribution

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


class ReplaceRefsSubjectsDumper(Dumper):
    """Replace linked subjects in document."""

    @staticmethod
    def _replace_subjects(data):
        """Replace the `$ref` linked subjects.

        :param data: dict - subjects data.
        """
        from rero_ils.modules.entities.api import Entity

        if not (entity := Entity.get_record_by_pid(data['pid'])):
            raise RecordNotFound(Entity, data['pid'])
        _type, _ = Entity.get_type_and_pid_from_ref(data['$ref'])
        contribution = deepcopy(data)
        contribution.update(dict(entity))
        contribution.update({
            'primary_source': _type,
            'pid': data['pid']
        })
        del contribution['$ref']
        return contribution

    def dump(self, record, data):
        """Dump record data by replacing linked subjects and imported subjects.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        entities = []
        for subject in [d['entity'] for d in data.get('subjects', [])]:
            subject_type = subject.get('type')
            subject_ref = subject.get('$ref')
            if subject_ref and subject_type in [
                EntityType.PERSON,
                EntityType.ORGANISATION
            ]:
                entities.append(dict(entity=self._replace_subjects(subject)))
            else:
                entities.append(dict(entity=subject))
        if entities:
            data['subjects'] = entities
        return data


class ReplaceRefsDumper(Dumper):
    """Replace link data in document."""

    def dump(self, record, data):
        """Dump record data by replacing `$ref` links.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        from copy import deepcopy
        return deepcopy(_records_state.replace_refs(data))
