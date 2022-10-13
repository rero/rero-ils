# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Stats configuration record extensions."""

from invenio_records.extensions import RecordExtension

from rero_ils.modules.patrons.api import Patron, current_librarian


class StatConfigDataExtension(RecordExtension):
    """Add related stats configuration data extension."""

    categories = {
        'number_of_checkouts': 'Circulation',
        'number_of_checkins': 'Circulation',
        'number_of_renewals': 'Circulation',
        'number_of_requests': 'Circulation',
        'number_of_documents': 'Catalogue',
        'number_of_created_documents': 'Catalogue',
        'number_of_items': 'Catalogue',
        'number_of_created_items': 'Catalogue',
        'number_of_deleted_items': 'Catalogue',
        'number_of_holdings': 'Catalogue',
        'number_of_created_holdings': 'Catalogue',
        'number_of_patrons': 'User management',
        'number_of_active_patrons': 'User management',
        'number_of_ill_requests': 'Circulation',
        'number_of_notifications': 'Administration'
    }

    def pre_create(self, record):
        """Add extra data to configuration.

        :param record: the record to add extra data.
        """
        if 'librarian_pid' not in record:
            record['org_pid'] = current_librarian.get_organisation().get('pid')
        else:
            librarian = Patron.get_record_by_pid(record['librarian_pid'])
            record['org_pid'] = librarian.get_organisation().get('pid')

        record['category'] = self.categories[record['indicator']]
        record['status'] = 'active'

        if not record['period']:
            record['period'] = 'month'
        if not record['frequency']:
            record['frequency'] = 'month'

        record.model.data = dict(record)
