# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Statistics configuration record extensions."""

from invenio_records.extensions import RecordExtension

from rero_ils.modules.stats_cfg.models import StatConfigurationStatus


class StatConfigDataExtension(RecordExtension):
    """Add related statistics configuration data extension."""

    categories_mapping = {
        'number_of_documents': 'catalogue',
        'number_of_serial_holdings': 'catalogue',
        'number_of_items': 'catalogue',
        'number_of_patrons': 'user_management',
        'number_of_active_patrons': 'user_management',
        'number_of_ill_requests': 'circulation',
        'number_of_deleted_items': 'catalogue',
        'number_of_checkouts': 'circulation',
        'number_of_checkins': 'circulation',
        'number_of_renewals': 'circulation',
        'number_of_requests': 'circulation'
    }

    def pre_create(self, record):
        """Add extra data to configuration.

        :param record: the record to add extra data.
        """
        record['category'] = self.categories_mapping[record.get('indicator')]
        if 'status' not in record:
            record['status'] = StatConfigurationStatus.ENABLED

        record.model.data = dict(record)
