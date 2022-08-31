# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized.

        Remove fields that can have a link to other records in the database.

        :param record: the record to analyze
        :param data: The dict passed to the record's constructor
        :param model: The model class used for initialization.
        """
        fields = ['pid']
        if record.get('template_type') == 'items':
            fields += ['barcode', 'status', 'document', 'holding',
                       'organisation', 'library']

        elif record.get('template_type') == 'holdings':
            fields += ['organisation', 'library', 'document']
        elif record.get('template_type') == 'patrons':
            fields += ['user_id', 'patron.subscriptions', 'patron.barcode']

        for field in fields:
            if '.' in field:
                level_1, level_2 = field.split('.')
                record.get('data', {}).get(level_1, {}).pop(level_2, None)
            else:
                record.get('data', {}).pop(field, None)
