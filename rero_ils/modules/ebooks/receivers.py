# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Signals connections for ebooks document."""

from dojson.contrib.marc21.utils import create_record
from flask import current_app

from .dojson.contrib.marc21 import marc21
from .tasks import create_records, delete_records
from ..utils import set_timestamp


def publish_harvested_records(sender=None, records=[], *args, **kwargs):
    """Create, index the harvested records."""
    # name = kwargs['name']
    max = kwargs.get('max', None)
    records = list(records)
    if max:
        records = records[:int(max)]
    converted_records = []
    deleted_records = []
    for record in records:
        rec = create_record(record.xml)
        rec = marc21.do(rec)
        rec.setdefault('harvested', True)

        identifiers = rec.get('identifiedBy', [])
        identifiers.append(
            {
                "type": "bf:Local",
                "source": "cantook",
                "value": record.header.identifier
            }
        )
        rec['identifiedBy'] = identifiers
        if record.deleted:
            deleted_records.append(rec)
        else:
            converted_records.append(rec)
    if converted_records:
        current_app.logger.info(
            'publish_harvester: received {count} records to create'
            .format(count=len(converted_records))
        )
        create_records(converted_records)
    if deleted_records:
        current_app.logger.info(
            'publish_harvester: received {count} records to delete'
            .format(count=len(deleted_records))
        )
        delete_records(deleted_records)
    msg = 'deleted: {delet_count}, created: {create_count}'.format(
        delet_count=len(deleted_records),
        create_count=len(converted_records)
    )
    set_timestamp('ebooks-harvester', msg=msg)
