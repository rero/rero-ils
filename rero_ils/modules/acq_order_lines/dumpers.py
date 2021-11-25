# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Acquisition order line dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper

from rero_ils.modules.acq_order_lines.models import AcqOrderLineNoteType
from rero_ils.modules.documents.utils import title_format_text_head


class AcqOrderLineESDumper(InvenioRecordsDumper):
    """ElasticSearch dumper class for an AcqOrderLine."""

    def dump(self, record, data):
        """Dump an AcqOrderLine instance for ElasticSearch.

        For ElasticSearch integration, we need to dump basic informations from
        a `AcqOrderLine` object instance, and add some data from related
        object : related account basic informations and related document basic
        informations.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        # Keep only some attributes from AcqOrderLine object initial dump.
        for attr in ['status', 'order_date', 'receipt_date', 'quantity']:
            value = record.get(attr)
            if value:
                data.update({attr: value})

        # Add account informations: pid, name and reference number.
        # (remove None values from account metadata)
        account = record.account
        data['account'] = {
            'pid': account.pid,
            'name': account['name'],
            'number': account.get('number')
        }
        data['account'] = {k: v for k, v in data['account'].items() if v}

        # Add document informations: pid, formatted title and ISBN identifiers.
        # (remove None values from document metadata)
        document = record.document
        data['document'] = {
            'pid': document.pid,
            'title': title_format_text_head(document.get('title', [])),
            'identifiers': document.get_identifier_values(filters=['bf:Isbn'])
        }
        data['document'] = {k: v for k, v in data['document'].items() if v}
        return data


class AcqOrderLineNotificationDumper(InvenioRecordsDumper):
    """Order line dumper class for acquisition order."""

    def dump(self, record, data):
        """Dump an AcqOrderLine instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        # Dumps AcqOrderLine acquisition
        data.update({
            'quantity': record.get('quantity'),
            'note': record.get_note(AcqOrderLineNoteType.VENDOR)
        })
        data = {k: v for k, v in data.items() if v}

        # Add document informations: formatted title and ISBN identifiers.
        document = record.document
        data['document'] = {
            'title': title_format_text_head(document.get('title', [])),
            'identifiers': document.get_identifier_values(filters=['bf:Isbn'])
        }
        data['document'] = {k: v for k, v in data['document'].items() if v}
        return data
