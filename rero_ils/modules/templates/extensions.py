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


class RemoveDataPidExtension(RecordExtension):
    """Defines the methods needed by an extension."""

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized.

        :param data: The dict passed to the record's constructor
        :param model: The model class used for initialization.
        """
        # force removing of record pid
        record.get('data', {}).pop('pid', None)
