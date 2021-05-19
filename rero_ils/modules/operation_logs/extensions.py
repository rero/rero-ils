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

"""Operation log record extensions."""
import uuid
from datetime import datetime

import pytz
from invenio_records.extensions import RecordExtension

from ..utils import extracted_data_from_ref


class ResolveRefsExension(RecordExtension):
    """Replace all $ref values by a dict of pid, type."""

    mod_type = {
        'documents': 'doc',
        'items': 'item',
        'holdings': 'hold'
    }

    def pre_dump(self, record, dumper=None):
        """Called before a record is dumped.

        :param record: the record metadata.
        :param dumper: the record dumper.
        """
        self._resolve_refs(record)

    def _resolve_refs(self, record):
        """Recursively replace the $refs.

        Replace in place all $ref to a dict of pid, type values.

        :param record: the record metadata.
        """
        for k, v in record.items():
            if isinstance(v, dict):
                if v.get('$ref'):
                    _type = self.mod_type.get(
                        extracted_data_from_ref(v, data='resource'))
                    if _type:
                        resolved = dict(
                            pid=extracted_data_from_ref(v),
                            type=_type
                        )
                        record[k] = resolved
                else:
                    self._resolve_refs(v)


class IDExtension(RecordExtension):
    """Generate an unique ID if does not exists."""

    def pre_create(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        if not record.get('pid'):
            record['pid'] = str(uuid.uuid1())


class DatesExension(RecordExtension):
    """Set the created and updated date if needed."""

    def pre_create(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        iso_now = pytz.utc.localize(datetime.utcnow()).isoformat()
        for date_field in ['_created', '_updated']:
            if not record.get(date_field):
                record[date_field] = iso_now
