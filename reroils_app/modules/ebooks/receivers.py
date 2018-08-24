# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Signals connections for ebooks document."""

from dojson.contrib.marc21.utils import create_record
from flask import current_app

from .dojson.contrib.marc21 import marc21
from .tasks import create_records


def publish_harvested_records(sender=None, records=[], *args, **kwargs):
    """Create, index the harvested records."""
    # name = kwargs['name']
    converted_records = []
    for record in records:
        if record.deleted:
            # TODO: remove record
            continue
        rec = create_record(record.xml)
        rec = marc21.do(rec)
        rec.setdefault('identifiers', {})['oai'] = record.header.identifier
        converted_records.append(rec)
    if records:
        current_app.logger.info('publish_harvester: received {} records'
                                .format(len(converted_records)))
        create_records(converted_records)
    else:
        current_app.logger.info('publish_harvester: nothing to do')
