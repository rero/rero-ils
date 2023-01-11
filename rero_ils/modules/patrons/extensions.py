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

"""Patron record extensions."""
from invenio_records.extensions import RecordExtension

from rero_ils.modules.users.api import User


class UserDataExtension(RecordExtension):
    """Add related user data extension."""

    def pre_dump(self, record, data, dumper=None):
        """Add user data.

        :param record: the record metadata.
        :param data: The dumped data dictionary.
        :param dumper: Dumper to use when dumping the record.
        :return the future dumped data.
        """
        user = User.get_record(record.get('user_id'))
        user_info = user.dumps_metadata()
        return data.update(user_info)
