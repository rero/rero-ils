# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

from ..models import DocumentSubjectType


class ReplaceRefsContributionsDumper(Dumper):
    """Replace linked contributions in document."""

    @staticmethod
    def _replace_contribution(data):
        """Replace the `$ref` linked contributions."""
        from rero_ils.modules.contributions.api import Contribution

        if entity := Contribution.get_record_by_pid(data['pid']):
            _type, _ = Contribution.get_type_and_pid_from_ref(data['$ref'])
            contribution = entity.dumps_for_document()
            contribution.update({
                'primary_source': _type,
                'pid': data['pid']
            })
            return contribution
        else:
            raise Exception(f'Contribution does not exists for {self.pid}')

    def dump(self, record, data):
        """Dump an item instance for notification.

        :param record: record to dump.
        :param data: initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        new_contributions = []
        for contribution in data.get('contribution', []):
            if not contribution['entity'].get('$ref'):
                new_contributions.append(contribution)
            else:
                new_contributions.append({
                    'entity': self._replace_contribution(
                        contribution['entity']),
                    'role': contribution['role']
                    })
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
        from rero_ils.modules.contributions.api import Contribution

        if not (entity := Contribution.get_record_by_pid(data['pid'])):
            raise Exception(f'Contribution does not exists for {data["pid"]}')

        _type, _ = Contribution.get_type_and_pid_from_ref(
            data['$ref'])
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
        for subjects in ['subjects', 'subjects_imported']:
            new_contributions = []
            for subject in data.get(subjects, []):
                subject_type = subject.get('type')
                subject_ref = subject.get('$ref')
                if subject_ref and subject_type in [
                    DocumentSubjectType.PERSON,
                    DocumentSubjectType.ORGANISATION
                ]:
                    new_contributions.append(
                        self._replace_subjects(subject))
                else:
                    new_contributions.append(subject)
            if new_contributions:
                data[subjects] = new_contributions
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
