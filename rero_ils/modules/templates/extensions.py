# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Template record extensions."""
from invenio_records.extensions import RecordExtension


class CleanDataDictExtension(RecordExtension):
    """Defines the methods needed by an extension."""

    fields_to_clean = {
        'documents': [
            'pid'
        ],
        'items': [
            'pid',
            'barcode',
            'status',
            'document',
            'holding',
            'organisation',
            'library'
        ],
        'holdings': [
            'pid',
            'organisation',
            'library',
            'document'
        ],
        'patrons': [
            'pid',
            'user_id',
            'patron.subscriptions',
            'patron.barcode'
        ]
    }

    def _clean_record(self, record):
        """Remove fields that can have a link to other records in the database.

        When storing a `Template`, we don't want to store possible residual
        links to other resource. Fields to clean depend on `Template` type.

        :param record: the record to analyze
        """

        def _clean(data, keys):
            """Inner recursive function to clean data (allow dotted path).

            :param data: the dictionary to clean.
            :param keys: the list of key to clean into the dictionary.
            """
            if not data:
                return
            for key in keys:
                if '.' in key:
                    root_path, child_path = key.split('.', 1)
                    _clean(data.get(root_path, {}), [child_path])
                else:
                    data.pop(key, None)

        if not record.get('data'):
            return
        if fields := self.fields_to_clean.get(record.get('template_type')):
            _clean(record['data'], fields)

    def pre_commit(self, record):
        """Called before a record is committed."""
        self._clean_record(record)

    def pre_create(self, record):
        """Called before a record is created."""
        self._clean_record(record)
        # DEV NOTE :: we need to update the model to store record modification
        # into the database ; otherwise this is the original data that will
        # be stored into database.
        if record.model:
            record.model.data = record
